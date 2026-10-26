import 'package:csit/core/network/api_client.dart';
import 'package:csit/features/announcements/data/announcements_api.dart';
import 'package:csit/features/notifications/data/notifications_api.dart';

/// بدائل في الذاكرة لاختبارات شاشات الإعلانات والإشعارات — بلا شبكة.

class FakeAnnouncementsApi implements AnnouncementsApi {
  FakeAnnouncementsApi({List<AnnouncementItem>? items, this.error})
      : items = items ?? const [];

  List<AnnouncementItem> items;
  ApiException? error;
  ApiException? markReadError;
  int feedCalls = 0;
  final List<String> readIds = [];

  @override
  Future<List<AnnouncementItem>> feed() async {
    feedCalls++;
    final failure = error;
    if (failure != null) {
      throw failure;
    }
    return items;
  }

  @override
  Future<void> markRead(String announcementId) async {
    readIds.add(announcementId);
    final failure = markReadError;
    if (failure != null) {
      throw failure;
    }
  }
}

class FakeNotificationsApi implements NotificationsApi {
  FakeNotificationsApi({
    List<NotificationItem>? items,
    int? unreadCount,
    this.error,
  })  : items = items ?? const [],
        unreadCount = unreadCount ??
            (items ?? const <NotificationItem>[])
                .where((item) => !item.isRead)
                .length;

  List<NotificationItem> items;
  int unreadCount;
  ApiException? error;
  ApiException? markReadError;
  ApiException? markAllError;
  int inboxCalls = 0;
  int markAllCalls = 0;
  final List<String> readIds = [];

  @override
  Future<NotificationInbox> inbox() async {
    inboxCalls++;
    final failure = error;
    if (failure != null) {
      throw failure;
    }
    return NotificationInbox(items: items, unreadCount: unreadCount);
  }

  @override
  Future<void> markRead(String notificationId) async {
    readIds.add(notificationId);
    final failure = markReadError;
    if (failure != null) {
      throw failure;
    }
  }

  @override
  Future<void> markAllRead() async {
    markAllCalls++;
    final failure = markAllError;
    if (failure != null) {
      throw failure;
    }
  }
}
