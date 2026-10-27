import 'package:flutter/widgets.dart';

/// مفتاح الملاحة الجذري — يسمح للإشعارات بفتح صندوق الوارد من أي شاشة
/// دون تمرير `BuildContext` عبر خدمات لا تعرف الواجهة.
final rootNavigatorKey = GlobalKey<NavigatorState>();
