import 'package:url_launcher/url_launcher.dart';

/// فتح رابط خارجي (تنزيل مادة أو فتح فيديو) — قابل للحقن في الاختبارات.
abstract class LinkOpener {
  Future<bool> open(Uri url);
}

/// تنفيذ حقيقي عبر url_launcher (متصفح الجهاز).
class UrlLauncherLinkOpener implements LinkOpener {
  const UrlLauncherLinkOpener();

  @override
  Future<bool> open(Uri url) async {
    try {
      return await launchUrl(url, mode: LaunchMode.externalApplication);
    } catch (_) {
      return false;
    }
  }
}
