"""
middleware.py

Middleware for handling country-specific payroll configurations.

This middleware attaches the active payroll country to each request and uses
caching to avoid repeated database queries, preventing race conditions.
"""

import logging
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class PayrollCountryMiddleware(MiddlewareMixin):
    """
    Middleware to attach the active payroll country to each request.
    
    This ensures consistent country detection across the entire request lifecycle.
    
    CRITICAL: All payroll calculations should use request.payroll_country
    instead of re-querying the database to prevent race conditions.
    """
    
    CACHE_KEY_PREFIX = 'payroll_active_country'
    CACHE_TIMEOUT = 300  # 5 minutes
    
    def process_request(self, request):
        """
        Attach payroll_country to request object.
        Uses caching to avoid repeated database queries.
        """
        # Get company_id from request/session if available
        company_id = None
        if hasattr(request, 'session'):
            selected_company = request.session.get('selected_company')
            if selected_company:
                # Handle Company object or ID
                if hasattr(selected_company, 'id'):
                    company_id = selected_company.id
                elif isinstance(selected_company, (int, str)):
                    # If it's 'all' or other string, treat as None
                    if str(selected_company).lower() != 'all':
                        try:
                            company_id = int(selected_company)
                        except (ValueError, TypeError):
                            company_id = None
        
        # Generate cache key based on company
        cache_key = f"{self.CACHE_KEY_PREFIX}_{company_id if company_id else 'global'}"
        
        # Try cache first
        cached_country = cache.get(cache_key)
        
        if cached_country is not None:
            request.payroll_country = cached_country
            logger.debug(f"Using cached payroll country: {cached_country.get('country', 'Unknown')}")
            return
        
        # Cache miss - query database
        try:
            from payroll.models.country_models import PayrollCountryConfig
            
            # Build filter kwargs
            filter_kwargs = {'is_active': True}
            if company_id is not None:
                filter_kwargs['company_id'] = company_id
            
            active_config = PayrollCountryConfig.objects.filter(
                **filter_kwargs
            ).select_related('activated_by').first()
            
            if active_config:
                country_data = {
                    'country': active_config.country,
                    'country_display': active_config.get_country_display(),
                    'activated_at': active_config.activated_at.isoformat() if hasattr(active_config, 'activated_at') and active_config.activated_at else None,
                    'company_id': company_id,
                }
                
                # Cache the result
                cache.set(cache_key, country_data, self.CACHE_TIMEOUT)
                request.payroll_country = country_data
                
                logger.debug(f"Cached payroll country: {country_data['country']}")
            else:
                # No active country - default to USA
                default_country = {
                    'country': 'USA',
                    'country_display': 'United States',
                    'activated_at': None,
                    'company_id': company_id,
                }
                
                cache.set(cache_key, default_country, self.CACHE_TIMEOUT)
                request.payroll_country = default_country
                
                logger.warning(f"No active payroll country config found for company {company_id}, defaulting to USA")
        
        except Exception as e:
            # Critical error - log but don't crash the request
            logger.error(f"Failed to get payroll country config: {e}", exc_info=True)
            
            # Set emergency fallback
            request.payroll_country = {
                'country': 'USA',
                'country_display': 'United States (Emergency Fallback)',
                'activated_at': None,
                'company_id': company_id,
                'error': str(e)
            }
    
    @staticmethod
    def clear_country_cache(company_id=None):
        """
        Clear the cached country configuration.
        Call this whenever PayrollCountryConfig is modified.
        
        Args:
            company_id: If provided, clears cache for specific company. 
                       If None, clears all cached countries.
        """
        if company_id is not None:
            cache_key = f"{PayrollCountryMiddleware.CACHE_KEY_PREFIX}_{company_id}"
            cache.delete(cache_key)
            logger.info(f"Cleared payroll country cache for company {company_id}")
        else:
            # Clear all possible cache keys (inefficient but thorough)
            # In production, consider using cache.delete_pattern if using Redis
            cache.delete(f"{PayrollCountryMiddleware.CACHE_KEY_PREFIX}_global")
            logger.info("Cleared global payroll country cache")
        
        # Also clear the global cache key
        cache.delete(f"{PayrollCountryMiddleware.CACHE_KEY_PREFIX}_None")
