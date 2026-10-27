import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_timezone/flutter_timezone.dart';
import 'package:timezone/data/latest.dart' as tz_data;
import 'package:timezone/timezone.dart' as tz;

import 'reminder_plan.dart';

/// غلاف رفيع حول إشعارات النظام: قناة واحدة، جدولة التذكيرات، وإظهار فوري.
///
/// الفصل عن `reminder_plan.dart` مقصود: منطق «متى نذكّر» يُختبر بلا منصة،
/// وهذا الملف هو الجزء الذي يلمس نظام التشغيل فقط.
class LocalNotificationService {
  LocalNotificationService({FlutterLocalNotificationsPlugin? plugin, this.onTap})
      : _plugin = plugin ?? FlutterLocalNotificationsPlugin();

  /// يُستدعى عند ضغط المستخدم على إشعار (نظام أو دفع) — payload يحمل نوعه.
  final void Function(String? payload)? onTap;

  static const channelId = 'csit_lectures';
  static const _notificationId = 5000;

  final FlutterLocalNotificationsPlugin _plugin;
  bool _initialized = false;

  bool get isInitialized => _initialized;

  Future<void> initialize({
    required String channelName,
    required String channelDescription,
  }) async {
    if (_initialized) {
      return;
    }
    tz_data.initializeTimeZones();
    try {
      final info = await FlutterTimezone.getLocalTimezone();
      tz.setLocalLocation(tz.getLocation(info.identifier));
    } catch (_) {
      // تعذّر قراءة منطقة الجهاز: نكمل بـUTC بدل إسقاط التذكيرات كلها
      tz.setLocalLocation(tz.UTC);
    }

    const android = AndroidInitializationSettings('@mipmap/ic_launcher');
    const darwin = DarwinInitializationSettings();
    await _plugin.initialize(
      settings: const InitializationSettings(android: android, iOS: darwin),
      onDidReceiveNotificationResponse: (response) => onTap?.call(response.payload),
    );

    final androidPlugin = _plugin.resolvePlatformSpecificImplementation<
        AndroidFlutterLocalNotificationsPlugin>();
    await androidPlugin?.createNotificationChannel(
      AndroidNotificationChannel(
        channelId,
        channelName,
        description: channelDescription,
        importance: Importance.high,
      ),
    );
    // أندرويد 13+: الإذن مطلوب؛ الرفض لا يُسقط التطبيق (الصندوق داخل التطبيق يبقى)
    await androidPlugin?.requestNotificationsPermission();
    _initialized = true;
  }

  NotificationDetails _details() => const NotificationDetails(
        android: AndroidNotificationDetails(
          channelId,
          'csit_lectures',
          channelDescription: 'csit lecture reminders',
          importance: Importance.high,
          priority: Priority.high,
        ),
        iOS: DarwinNotificationDetails(),
      );

  Future<void> schedule(ReminderPlan plan) async {
    if (!_initialized) {
      return;
    }
    await _plugin.cancelAll();
    for (final reminder in plan.reminders) {
      await _plugin.zonedSchedule(
        id: reminder.id,
        scheduledDate: tz.TZDateTime.from(reminder.at, tz.local),
        notificationDetails: _details(),
        androidScheduleMode: AndroidScheduleMode.inexactAllowWhileIdle,
        title: reminder.title,
        body: reminder.body,
        payload: 'csit.reminder',
      );
    }
  }

  Future<void> cancelAll() async {
    if (!_initialized) {
      return;
    }
    await _plugin.cancelAll();
  }

  /// إظهار إشعار فوري (رسالة FCM في المقدمة).
  Future<void> showNow({required String title, required String body}) async {
    if (!_initialized) {
      return;
    }
    await _plugin.show(
      id: _notificationId,
      title: title,
      body: body,
      notificationDetails: _details(),
      payload: 'csit.push',
    );
  }
}
