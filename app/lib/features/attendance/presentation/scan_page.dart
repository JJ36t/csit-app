import 'dart:async';

import 'package:flutter/material.dart';

import '../../../core/network/api_client.dart';
import '../../../core/utils/date_utils.dart';
import '../../../l10n/app_localizations.dart';
import '../../auth/presentation/session.dart';
import '../data/attendance_api.dart';
import '../data/attendance_scanner.dart';
import '../data/location_service.dart';
import '../data/qr_payload.dart';

/// شاشة مسح الحضور للطالب: كاميرا + نتيجة آخر مسح (نموذج الشاشة 4).
///
/// الماسح وخدمة الموقع قابلان للحقن كي تُختبر الشاشة ببدائل في الذاكرة.
class ScanPage extends StatefulWidget {
  const ScanPage({
    super.key,
    required this.api,
    required this.session,
    this.scanner,
    this.locationService,
  });

  final AttendanceApi api;
  final SessionController session;
  final AttendanceScanner? scanner;
  final LocationService? locationService;

  @override
  State<ScanPage> createState() => _ScanPageState();
}

class _ScanPageState extends State<ScanPage> {
  late final AttendanceScanner _scanner =
      widget.scanner ?? MobileScannerAttendanceScanner();
  late final LocationService _locationService =
      widget.locationService ?? const GeolocatorLocationService();
  StreamSubscription<String>? _subscription;

  bool _submitting = false;
  ScanResult? _result;
  DateTime? _resultAt;
  String? _error;

  ScanLocation? _cachedLocation;
  DateTime? _cachedLocationAt;

  @override
  void initState() {
    super.initState();
    _subscription = _scanner.codes.listen(_onCode);
  }

  @override
  void dispose() {
    _subscription?.cancel();
    _scanner.dispose();
    super.dispose();
  }

  Future<void> _onCode(String raw) async {
    if (!mounted || _submitting) {
      return;
    }
    final l10n = AppLocalizations.of(context)!;
    final payload = QrPayload.tryParse(raw);
    if (payload == null) {
      setState(() => _error = l10n.invalidQrError);
      return;
    }
    setState(() {
      _submitting = true;
      _error = null;
    });
    try {
      final location = await _currentLocation();
      final result = await widget.api.scan(
        sessionId: payload.sessionId,
        token: payload.token,
        location: location,
      );
      if (!mounted) {
        return;
      }
      setState(() {
        _result = result;
        _resultAt = DateTime.now().toUtc();
      });
    } on ApiException catch (error) {
      if (!mounted) {
        return;
      }
      if (error.statusCode == 401) {
        widget.session.expire();
        return;
      }
      setState(() => _error = error.messageAr ?? _messageFor(l10n, error.code));
    } catch (_) {
      if (!mounted) {
        return;
      }
      setState(() => _error = l10n.unexpectedError);
    } finally {
      if (mounted) {
        setState(() => _submitting = false);
      }
    }
  }

  String _messageFor(AppLocalizations l10n, String code) {
    switch (code) {
      case 'network_unreachable':
        return l10n.networkUnreachable;
      case 'missing_device_id':
        return l10n.missingDeviceError;
      case 'session_expired':
      case 'not_authenticated':
        return l10n.sessionExpired;
      default:
        return l10n.unexpectedError;
    }
  }

  /// موقع بأفضل جهد مع كاش 60 ثانية — تعطّره لا يمنع المسح.
  Future<ScanLocation?> _currentLocation() async {
    final cached = _cachedLocation;
    final cachedAt = _cachedLocationAt;
    if (cached != null &&
        cachedAt != null &&
        DateTime.now().toUtc().difference(cachedAt) < const Duration(seconds: 60)) {
      return cached;
    }
    final location = await _locationService.current();
    if (location != null) {
      _cachedLocation = location;
      _cachedLocationAt = DateTime.now().toUtc();
    }
    return location;
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final theme = Theme.of(context);
    final result = _result;

    return Scaffold(
      appBar: AppBar(title: Text(l10n.scanTitle)),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            AspectRatio(
              aspectRatio: 1,
              child: ClipRRect(
                borderRadius: BorderRadius.circular(16),
                child: Stack(
                  fit: StackFit.expand,
                  children: [
                    _scanner.buildPreview(),
                    const IgnorePointer(
                      child: DecoratedBox(
                        decoration: ShapeDecoration(
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.all(Radius.circular(16)),
                            side: BorderSide(color: Colors.white70, width: 2),
                          ),
                        ),
                      ),
                    ),
                    if (_submitting)
                      ColoredBox(
                        color: Colors.black38,
                        child: Center(
                          child: CircularProgressIndicator(
                            color: theme.colorScheme.onPrimary,
                          ),
                        ),
                      ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
            Text(
              l10n.scannerHint,
              key: const Key('scannerHint'),
              textAlign: TextAlign.center,
              style: theme.textTheme.titleSmall,
            ),
            const SizedBox(height: 4),
            Text(
              l10n.scanHelp,
              textAlign: TextAlign.center,
              style: theme.textTheme.bodySmall,
            ),
            const SizedBox(height: 16),
            if (_error != null) ...[
              Container(
                key: const Key('scanError'),
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: theme.colorScheme.errorContainer,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  _error!,
                  style:
                      TextStyle(color: theme.colorScheme.onErrorContainer),
                ),
              ),
              const SizedBox(height: 16),
            ],
            if (result != null && _resultAt != null)
              _ResultCard(result: result, at: _resultAt!),
            const SizedBox(height: 16),
            Row(
              children: [
                Icon(Icons.lock_outline,
                    size: 16, color: theme.colorScheme.outline),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    l10n.deviceNote,
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: theme.colorScheme.outline,
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

/// بطاقة «نتيجة آخر مسح»: الحالة والرسالة وسبب التعليم عند وجوده.
class _ResultCard extends StatelessWidget {
  const _ResultCard({required this.result, required this.at});

  final ScanResult result;
  final DateTime at;

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final theme = Theme.of(context);

    final flagged = result.flagged;
    final status = flagged ? 'flagged' : result.status;

    final (icon, color) = switch (status) {
      'present' => (Icons.check_circle_outlined, const Color(0xFF1B7A55)),
      'late' => (Icons.schedule_outlined, const Color(0xFF8A4B00)),
      _ => (Icons.warning_amber_outlined, const Color(0xFFB3261E)),
    };
    final title = switch (status) {
      'present' => l10n.presentStatus,
      'late' => l10n.lateStatus,
      _ => l10n.flaggedStatus,
    };
    final reasonText = flagged
        ? _flagReasonText(l10n, result.flagReason)
        : null;

    return Card(
      key: const Key('scanResultCard'),
      margin: EdgeInsets.zero,
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(l10n.lastScanResult, style: theme.textTheme.labelMedium),
                Text(formatHm(at), style: theme.textTheme.labelMedium),
              ],
            ),
            const SizedBox(height: 10),
            Row(
              children: [
                Icon(icon, size: 40, color: color),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        title,
                        key: const Key('scanResultTitle'),
                        style: theme.textTheme.titleLarge
                            ?.copyWith(color: color, fontWeight: FontWeight.bold),
                      ),
                      if (result.messageAr.isNotEmpty) ...[
                        const SizedBox(height: 2),
                        Text(result.messageAr,
                            style: theme.textTheme.bodySmall),
                      ],
                      if (reasonText != null) ...[
                        const SizedBox(height: 2),
                        Text(
                          reasonText,
                          key: const Key('scanFlagReason'),
                          style: theme.textTheme.bodySmall
                              ?.copyWith(color: color),
                        ),
                      ],
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                _LegendDot(
                    label: l10n.presentStatus,
                    color: const Color(0xFF1B7A55),
                    active: status == 'present'),
                const SizedBox(width: 12),
                _LegendDot(
                    label: l10n.lateStatus,
                    color: const Color(0xFF8A4B00),
                    active: status == 'late'),
                const SizedBox(width: 12),
                _LegendDot(
                    label: l10n.flaggedStatus,
                    color: const Color(0xFFB3261E),
                    active: status == 'flagged'),
              ],
            ),
          ],
        ),
      ),
    );
  }

  String? _flagReasonText(AppLocalizations l10n, String? reason) {
    if (reason == null) {
      return null;
    }
    if (reason == 'no_location') {
      return l10n.flagNoLocation;
    }
    final match = RegExp(r'^outside_campus:(\d+)m$').firstMatch(reason);
    if (match != null) {
      return l10n.flagOutsideCampus(int.parse(match.group(1)!));
    }
    return reason;
  }
}

class _LegendDot extends StatelessWidget {
  const _LegendDot({
    required this.label,
    required this.color,
    required this.active,
  });

  final String label;
  final Color color;
  final bool active;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 8,
          height: 8,
          decoration: BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 4),
        Text(
          label,
          style: theme.textTheme.bodySmall?.copyWith(
            color: active ? color : theme.colorScheme.outline,
            fontWeight: active ? FontWeight.bold : FontWeight.normal,
          ),
        ),
      ],
    );
  }
}
