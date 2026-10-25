import 'package:geolocator/geolocator.dart';

/// إحداثيات المسح كما تتوقعها نقطة `/attendance/scan`.
class ScanLocation {
  const ScanLocation({required this.lat, required this.lng, this.accuracyM});

  final double lat;
  final double lng;
  final double? accuracyM;

  Map<String, dynamic> toJson() => {
        'lat': lat,
        'lng': lng,
        if (accuracyM != null) 'accuracy_m': accuracyM,
      };
}

/// خدمة الموقع — الموقع اختياري بحسب الخطة (N1):
/// تعذّر الحصول عليه لا يمنع المسح؛ الخادم يعلم الحضور «مشكوكاً» للمراجعة.
abstract class LocationService {
  Future<ScanLocation?> current({
    Duration timeout = const Duration(seconds: 5),
  });
}

/// تنفيذ بـgeolocator: صلاحية عند الطلب، وقراءة واحدة بأفضل دقة متاحة.
class GeolocatorLocationService implements LocationService {
  const GeolocatorLocationService();

  @override
  Future<ScanLocation?> current({
    Duration timeout = const Duration(seconds: 5),
  }) async {
    try {
      var permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
      }
      if (permission != LocationPermission.whileInUse &&
          permission != LocationPermission.always) {
        return null;
      }
      final position = await Geolocator.getCurrentPosition(
        locationSettings:
            const LocationSettings(accuracy: LocationAccuracy.medium),
      ).timeout(timeout);
      final accuracy = position.accuracy;
      return ScanLocation(
        lat: position.latitude,
        lng: position.longitude,
        // حدّ الخادم: accuracy_m بين 0 و5000 — خارجه تُرسَل بلا دقة.
        accuracyM:
            accuracy >= 0 && accuracy <= 5000 ? accuracy.toDouble() : null,
      );
    } catch (_) {
      // أي فشل (خدمة الموقع مطفأة، مهلة، رفض صلاحية) = مسح بلا موقع.
      return null;
    }
  }
}
