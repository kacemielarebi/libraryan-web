from django.urls import path
from . import views
from .customer_views import (    list_customers_view,    customer_detail_view,
    create_customer_view,    update_customer_view,    delete_customer_view,)
from .auth_views import ( get_csrf_token_view,    login_view,    logout_view,    me_view,)
from .Notification_view import (CustomerNotificationsListView, MarkCustomerNotificationReadView,
    AdminNotificationsListView, MarkAdminNotificationReadView, unread_notifications_count)
urlpatterns = [
path('notifications/', CustomerNotificationsListView.as_view(), name='customer-notifications'),
    path('notifications/<int:pk>/read/', MarkCustomerNotificationReadView.as_view(), name='mark-customer-notification-read'),

    # إشعارات المشرف
    path('admin-notifications/', AdminNotificationsListView.as_view(), name='admin-notifications'),
    path('admin-notifications/<int:pk>/read/', MarkAdminNotificationReadView.as_view(), name='mark-admin-notification-read'),

    # عدد الإشعارات غير المقروءة
    path('notifications/unread-count/', unread_notifications_count, name='unread-notifications-count'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('me/', me_view, name='me'),
    path('csrf-token/', get_csrf_token_view, name='csrf_token'),
    path('categories/', views.CategoryListCreateView.as_view(), name='categories_list_create'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('books/', views.BookListView.as_view(), name='books_list'),
    path('books/create/', views.BookCreateView.as_view(), name='books_create'),
    path('books/<int:pk>/', views.BookDetailView.as_view(), name='books_detail'),
    path("books/<int:pk>/", views.BookRetrieveUpdateDestroyView.as_view(), name="book-detail"),
    path('books/<int:book_id>/view/', views.add_view, name='book_add_view'),
    path('books/<int:book_id>/read/', views.add_reading, name='book_add_reading'),
    path('books/<int:book_id>/download/', views.download_book_view, name='book_download'),
    path('books/<int:book_id>/favorite/', views.toggle_favorite_view, name='book_toggle_favorite'),
    path('books/<int:book_id>/rate/', views.rate_book, name='book_rate'),
    path('books/<int:book_id>/stats/', views.book_stats, name='book_stats'),
    path('books/top/', views.top_books, name='top_books'),
    path('favorites/', views.FavoriteListView.as_view(), name='favorites_list'),
    path('my-library/', views.my_library_view, name='my_library'),
    path('statistics/', views.StatisticsView.as_view(), name='statistics'),
    path("announcements/", views.AnnouncementListView.as_view(), name="announcements_list"),
    path("announcements/create/", views.AnnouncementCreateView.as_view(), name="announcements_create"),
    path(
        "announcements/<int:pk>/",
        views.AnnouncementDetailView.as_view(),
        name="announcements_detail"
    ),
    path('company-info/', views.CompanyInfoView.as_view(), name='company_info'),
     path('company-info/update/', views.CompanyInfoUpdateView.as_view(), name='company-info-update'),
    path('library-info/', views.LibraryInfoView.as_view(), name='library_info'),
    path('customers/', list_customers_view, name='customers_list'),
    path('customers/create/', create_customer_view, name='customers_create'),
    path('customers/<int:customer_id>/', customer_detail_view, name='customers_detail'),
path('customers/update/', update_customer_view, name='customers_update'),
    path('customers/delete/<int:customer_id>/', delete_customer_view, name='customers_delete'),
path('my-books-stats/', views.my_books_stats, name='my_books_stats'),
path('printed-copies/', views.PrintedCopyListCreateView.as_view(), name='printedcopy-list-create'),
    path('printed-copies/<int:pk>/', views.PrintedCopyRetrieveUpdateDestroyView.as_view(), name='printedcopy-detail'),
    path("print-requests/", views.PrintedCopyRequestListView.as_view()),
    path("print-requests/create/", views.PrintedCopyRequestCreateView.as_view()),
    path("print-requests/<int:pk>/update/", views.PrintedCopyRequestUpdateView.as_view()),
    path("print-requests/<int:pk>/delete/", views.PrintedCopyRequestDeleteView.as_view()),
]
