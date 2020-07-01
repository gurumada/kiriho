from django.urls import path
from unlimited import views


app_name = 'unlimited'
urlpatterns = [
    path('', views.Landing.as_view(), name='landing'),
    path('login/', views.Login.as_view(), name='login'),
    path('logout/', views.Logout.as_view(), name='logout'),
    path('user_create/', views.UserCreate.as_view(), name='user_create'),
    path('user_create/done/', views.UserCreateDone.as_view(), name='user_create_done'),
    path('user_create/complete/<token>/', views.UserCreateComplete.as_view(), name='user_create_complete'),
    path('user_detail/<int:pk>/', views.UserDetail.as_view(), name='user_detail'),
    path('user_update/<int:pk>/', views.UserUpdate.as_view(), name='user_update'),
    path('password_change/', views.PasswordChange.as_view(), name='password_change'),
    path('password_change/done/', views.PasswordChangeDone.as_view(), name='password_change_done'),
    path('password_reset/', views.PasswordReset.as_view(), name='password_reset'),
    path('password_reset/done/', views.PasswordResetDone.as_view(), name='password_reset_done'),
    path('password_reset/confirm/<uidb64>/<token>/', views.PasswordResetConfirm.as_view(), name='password_reset_confirm'),
    path('password_reset/complete/', views.PasswordResetComplete.as_view(), name='password_reset_complete'),
    path('email/change/', views.EmailChange.as_view(), name='email_change'),
    path('email/change/done/', views.EmailChangeDone.as_view(), name='email_change_done'),
    path('email/change/complete/<str:token>/', views.EmailChangeComplete.as_view(), name='email_change_complete'),

    path('salon_list/', views.SalonListView.as_view(), name='salon_list'),
    path('salon_update/<int:pk>/', views.SalonUpdateView.as_view(), name='salon_update'),
    path('salon_update/complete/', views.SalonUpdateComplete.as_view(), name='salon_update_complete'),
    path('stylist_list/', views.StylistList.as_view(), name='stylist_list'),
    path('stylist_detail/<int:pk>/', views.StylistDetail.as_view(), name='stylist_detail'),
    path('stylist_create/<int:affiliation_salon_id>/', views.StylistCreate.as_view(), name='stylist_create'),
    path('stylist_delete/<int:pk>/', views.StylistDelete.as_view(), name='stylist_delete'),
    path('reservation_create/<int:salon_id>/<str:user_name>', views.ReservationCreate.as_view(),
         name='reservation_create'),
    path('reservation_user_search/', views.UserSearch.as_view(), name='user_search'),
    path('reservation_create/complete/', views.ReservationCreateComplete.as_view(), name='reservation_create_complete'),
    path('reservation_update/<int:reservation_id>/', views.reservation_update, name='reservation_update'),
    path('dashboard/<int:pk>/', views.Dashboard.as_view(), name='dashboard'),
    path('privacy_policy/', views.PrivacyPolicy.as_view(), name='privacy_policy'),
    path('terms_of_service/', views.TermsOfService.as_view(), name='terms_of_service'),
    path('transaction_law/', views.TransactionLaw.as_view(), name='transaction_law'),
    path('distribution/', views.distribution, name='distribution'),

]
