import 'package:csit/core/network/api_client.dart';
import 'package:csit/core/platform/link_opener.dart';
import 'package:csit/features/grades/data/grades_api.dart';
import 'package:csit/features/materials/data/materials_api.dart';
import 'package:csit/features/timetable/data/timetable_api.dart';

/// بدائل في الذاكرة لاختبارات شاشات N2 — بلا شبكة ولا تخزين حقيقي.

class FakeTimetableApi implements TimetableApi {
  FakeTimetableApi({this.data, this.error});

  TimetableData? data;
  ApiException? error;
  int calls = 0;

  @override
  Future<TimetableData> load({DateTime? from, DateTime? to}) async {
    calls++;
    final failure = error;
    if (failure != null) {
      throw failure;
    }
    return data ??
        const TimetableData(sessions: [], changes: [], fromCache: false);
  }
}

class MemoryTimetableCache implements TimetableCache {
  ({List<SessionItem> items, DateTime at})? stored;

  @override
  Future<void> save(List<SessionItem> items, DateTime at) async {
    stored = (items: items, at: at);
  }

  @override
  Future<({List<SessionItem> items, DateTime at})?> read() async => stored;
}

class FakeMaterialsApi implements MaterialsApi {
  FakeMaterialsApi({
    List<OfferingSummary>? offerings,
    Map<String, List<MaterialItem>>? materials,
    this.offeringsError,
    this.materialsError,
  })  : offerings = offerings ?? const [],
        _materials = materials ?? const {};

  final List<OfferingSummary> offerings;
  final Map<String, List<MaterialItem>> _materials;
  ApiException? offeringsError;
  ApiException? materialsError;
  int offeringsCalls = 0;
  int materialsCalls = 0;

  @override
  Future<List<OfferingSummary>> myOfferings() async {
    offeringsCalls++;
    final failure = offeringsError;
    if (failure != null) {
      throw failure;
    }
    return offerings;
  }

  @override
  Future<MaterialsData> materials(String offeringId) async {
    materialsCalls++;
    final failure = materialsError;
    if (failure != null) {
      throw failure;
    }
    return MaterialsData(items: _materials[offeringId] ?? const []);
  }
}

class FakeGradesApi implements GradesApi {
  FakeGradesApi({this.courses, this.error});

  List<GradeCourse>? courses;
  ApiException? error;
  int calls = 0;

  @override
  Future<List<GradeCourse>> myGrades() async {
    calls++;
    final failure = error;
    if (failure != null) {
      throw failure;
    }
    return courses ?? const [];
  }
}

class FakeLinkOpener implements LinkOpener {
  FakeLinkOpener({this.result = true});

  bool result;
  final List<Uri> opened = [];

  @override
  Future<bool> open(Uri url) async {
    opened.add(url);
    return result;
  }
}
