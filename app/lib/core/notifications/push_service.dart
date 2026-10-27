import 'dart:async';

import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter/foundation.dart';

import '../../features/notifications/data/notifications_api.dart';
import 'local_notifications.dart';

/// تسجيل الجهاز في FCM وعرض الرسائل الواردة أثناء فتح التطبيق.
///
/// يعمل «بأفضل جهد»: إن غاب `google-services.json` أو رفض المستخدم الإذن،
/// يعود `false` ويكمل التطبيق بصندوق الإشعارات الداخلي وحده. لا نرمي استثناءً
/// كي لا يتحول غياب إعداد Firebase إلى شاشة بيضاء.
class PushService {
  PushService({required this.notifications, this.local, this.onOpen});

  final NotificationsApi notifications;
  final LocalNotificationService? local;

  /// يُستدعى عند فتح التطبيق من إشعار نظام (الضغط على الإشعار).
  final void Function(String? payload)? onOpen;
  StreamSubscription<RemoteMessage>? _foreground;
  StreamSubscription<RemoteMessage>? _opened;
  StreamSubscription<String>? _refresh;

  bool get isSupported => !kIsWeb;

  Future<bool> initialize() async {
    if (kIsWeb) {
      return false;
    }
    try {
      await Firebase.initializeApp();
      final messaging = FirebaseMessaging.instance;
      final settings = await messaging.requestPermission();
      if (settings.authorizationStatus == AuthorizationStatus.denied) {
        return false;
      }

      // firebase_messaging 17 يوجّه إلى onRegistered/FID، لكن مُرسِل الخادم
      // يعمل برمز FCM الكلاسيكي؛ نبقى عليه حتى ننتقل إلى واجهة FID.
      // ignore: deprecated_member_use
      final token = await messaging.getToken();
      if (token != null && token.isNotEmpty) {
        await notifications.registerFcmToken(token);
      }

      // ignore: deprecated_member_use
      _refresh ??= messaging.onTokenRefresh.listen((newToken) {
        unawaited(notifications.registerFcmToken(newToken));
      });

      _foreground ??= FirebaseMessaging.onMessage.listen((message) {
        final notification = message.notification;
        if (notification == null) {
          return;
        }
        unawaited(
          local?.showNow(
                title: notification.title ?? '',
                body: notification.body ?? '',
              ) ??
              Future<void>.value(),
        );
      });

      // الضغط على إشعار والد التطبيق مغلق → يفتح صندوق الإشعارات
      _opened ??= FirebaseMessaging.onMessageOpenedApp.listen((message) {
        onOpen?.call(message.data['type'] ?? 'push');
      });
      return true;
    } catch (_) {
      // إعداد Firebase غير مكتمل على هذا البناء — الميزة اختيارية بحسب الخطة
      return false;
    }
  }

  Future<void> dispose() async {
    await _foreground?.cancel();
    await _opened?.cancel();
    await _refresh?.cancel();
    _foreground = null;
    _opened = null;
    _refresh = null;
  }
}
