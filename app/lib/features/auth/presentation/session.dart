import 'package:flutter/foundation.dart';

import '../data/auth_repository.dart';

/// حالة الجلسة المشتركة — يراها الموجّه ليعيد التوجيه حسب الدخول.
class SessionController extends ChangeNotifier {
  SessionController(this._api);

  final AuthApi _api;

  UserProfile? _profile;
  bool _restoring = false;
  bool _busy = false;

  UserProfile? get profile => _profile;

  bool get isAuthenticated => _profile != null;

  bool get isRestoring => _restoring;

  bool get isBusy => _busy;

  /// استعادة الجلسة عند الإقلاع (إن وُجد رمز تجديد صالح).
  Future<void> restore() async {
    _restoring = true;
    notifyListeners();
    try {
      if (await _api.hasSession()) {
        _profile = await _api.me();
      }
    } catch (_) {
      _profile = null;
    } finally {
      _restoring = false;
      notifyListeners();
    }
  }

  Future<UserProfile> login({
    required String universityId,
    required String password,
  }) async {
    _busy = true;
    notifyListeners();
    try {
      final profile = await _api.login(
        universityId: universityId,
        password: password,
      );
      _profile = profile;
      return profile;
    } finally {
      _busy = false;
      notifyListeners();
    }
  }

  Future<void> logout() async {
    _busy = true;
    notifyListeners();
    try {
      await _api.logout();
    } finally {
      _profile = null;
      _busy = false;
      notifyListeners();
    }
  }

  /// تغيير كلمة المرور: الخادم يُلغي كل الجلسات — فتُمسح الحالة وتُعاد للدخول.
  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    _busy = true;
    notifyListeners();
    try {
      await _api.changePassword(
        currentPassword: currentPassword,
        newPassword: newPassword,
      );
      _profile = null;
    } finally {
      _busy = false;
      notifyListeners();
    }
  }

  /// انتهاء الجلسة قسرياً (فشل التجديد بعد 401) — الموجّه يعيد المستخدم للدخول.
  void expire() {
    if (_profile != null) {
      _profile = null;
      notifyListeners();
    }
  }
}
