"""
handbook/sidebar.py

To set Horilla sidebar for handbook
"""

from django.urls import reverse
from django.utils.translation import gettext_lazy as trans

MENU = trans("Handbook")
IMG_SRC = "images/ui/book-solid.svg"  # Use a book icon

SUBMENUS = [
    {
        "menu": trans("Chat Assistant"),
        "redirect": reverse("handbook-dashboard"),
    },
    {
        "menu": trans("Documents"),
        "redirect": reverse("handbook-documents"),
        "accessibility": "handbook.sidebar.document_accessibility",
    },
    {
        "menu": trans("Upload Document"),
        "redirect": reverse("handbook-upload"),
        "accessibility": "handbook.sidebar.upload_accessibility",
    },
]


def document_accessibility(request, submenu, user_perms, *args, **kwargs):
    """
    Check if user can view handbook documents
    """
    return user_perms.user.has_perm('handbook.view_handbookdocument') or user_perms.user.is_staff


def upload_accessibility(request, submenu, user_perms, *args, **kwargs):
    """
    Check if user can upload handbook documents
    """
    return user_perms.user.has_perm('handbook.add_handbookdocument') or user_perms.user.is_staff