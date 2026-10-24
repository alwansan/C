# تشخيص مشكلة تشغيل Naruto S01 E116 1080p في Cinemana

**تاريخ التحليل:** 24 أكتوبر 2026  
**مصدر بيانات الفيديو:** مستودع المستخدم `alwansan/C` — `REPORT_ALL_FILES.json` و`REPORT_ALL_FILES.txt` والتقارير الفردية الخمسة.  
**مرجع المشغل:** مشروع Cinemana PATCH242 المتاح في المكتبة (مصدر مفكك Smali)، وليس مصدر 245.

## النتيجة

الفرق الأقوى الذي يفسّر الفشل هو **H.264 High 10 / 10-bit** في نسختي 1080p للحلقة 116. أما الملفات الثلاثة التي تعمل (حلقة 116 بدقة 240p بصيغتي MP4 وMKV، وحلقة 220 بصيغة MKV بدقة 1280×960) فتستخدم **H.264 High / 8-bit**.

هذا يرجّح أن Decoder الفيديو الذي يستخدمه Android/ExoPlayer على الجهاز لا يقبل ترميز High 10 لهذا المسار. لا يمكن الجزم من تقرير FFmpeg وحده بأن العتاد لا يدعمه؛ يلزم قراءة قدرات MediaCodec الفعلية على الجهاز أو التقاط خطأ المشغل.

## مقارنة الملفات الخمسة

| الملف | الحاوية | الفيديو | الدقة | العمق | Level | FPS | نتيجة FFmpeg |
|---|---|---|---:|---:|---:|---:|---|
| E116 1080p MKV | MKV | H.264 High 10 | 1920×1080 | 10-bit | 5.0 | 23.976 | نجح |
| E116 240p MKV | MKV | H.264 High | 426×240 | 8-bit | 2.1 | 23.976 | نجح |
| E116 1080p MP4 | MP4 | H.264 High 10 | 1920×1080 | 10-bit | 5.0 | 23.976 | نجح |
| E116 240p MP4 | MP4 | H.264 High | 426×240 | 8-bit | 2.1 | 23.976 | نجح |
| E220 1080p MKV | MKV | H.264 High | 1280×960 | 8-bit | 4.0 | 29.970 | نجح |

جميع الملفات تستخدم AAC-LC بصوت ستيريو 48 kHz. عينات حزم الفيديو لم تسجل DTS regressions. نجح فك عينة من بداية ونهاية المسار المرئي/الصوتي في جميع الملفات.

## استبعاد الأسباب الأخرى

1. **الحاوية ليست السبب المرجّح:** نسخة E116 1080p تفشل بصيغتي MP4 وMKV، ونسخة 240p تعمل بصيغتيهما. العامل المشترك في النسختين الفاشلتين هو High 10 / 10-bit.
2. **زيادة مدة MKV ليست سبب الفشل:** ترجمتا E116 MKV تمتدان إلى 23:03.434 تقريبًا، بينما مسارا الفيديو والصوت إلى 22:39.54. النسخة 240p MKV لديها الظاهرة نفسها لكنها تعمل.
3. **تحذير UDTA في MP4 ليس سببًا مثبتًا:** يظهر مع MP4 1080p وكذلك MP4 240p، وكلا اختبارَي FFmpeg ينتهيان برمز نجاح 0.
4. **التوقيت ليس مؤشرًا قويًا للفشل:** MP4 1080p و240p لهما DTS أولي للفيديو يقارب -0.083 ثانية، كما توجد طوابع صوت سالبة صغيرة في MP4. نسخة 240p التي تعمل تُظهر ذلك أيضًا. لا توجد رجوعات DTS في العينات.
5. **الصوت ليس الاختلاف الفاصل:** مواصفات AAC-LC الأساسية متطابقة عمليًا بين الملفات.

## ما وجدته في مشغل PATCH242

- مصنع الرندرات `to0` معلّق بالمصدر `DefaultRenderersFactory.java`.
- داخل `to0.a(...)` ينشئ `yo2`، وهو `MediaCodecVideoRenderer`.
- معامل `enableDecoderFallback` يمرّر كقيمة `false` (`const/4 v7, 0x0` في Smali قبل إنشاء `yo2`).
- لم أجد `FfmpegVideoRenderer` أو `LibvpxVideoRenderer` أو `Libvlc` أو `ijkplayer` أو `mpv` كـVideo Renderer مضمّن في حزمة PATCH242 المفككة.
- وجود `libffmpeg.so` وبعض أدوات FFmpeg في التطبيق لا يثبت أنها موصولة بمسار العرض؛ كود المشغل المسحوب هنا يعتمد MediaCodec/ExoPlayer.

## التعديل الموصى به

1. تفعيل `enableDecoderFallback = true` في مصنع الرندرات. هذا يسمح بتجربة Decoder أقل أولوية إذا فشلت تهيئة الأول، لكنه لا ينشئ Decoder برمجيًا ولا يضمن High 10 إن لم يوجد Decoder متوافق.
2. إضافة تسجيل أخطاء واضح من ExoPlayer: `DecoderInitializationException`، واسم Decoder، و`MediaCodec.CodecException`، وحالة `onPlayerError`. يجب إنهاء حالة التحميل وعرض خطأ قابل للتشخيص بدل الدوران بلا نهاية.
3. قبل التشغيل أو بعد فشل MediaCodec، الاستعلام عن دعم تنسيق AVC High10 باستخدام `MediaCodecList` / `findDecoderForFormat` وملفات `profileLevels` على الجهاز.
4. إذا لم يوجد Decoder نظامي يدعم High10، توفير Video Renderer برمجي حقيقي (مبني على FFmpeg/libavcodec أو Backend مثل libVLC/mpv) كخيار احتياطي، مع إبقاء MediaCodec المسار الافتراضي للفيديوهات العادية. فك 1080p برمجيًا قد يستهلك بطارية وحرارة أكثر.

## الاختبار الإضافي الحاسم

للعزل النهائي بين High10 وبين الدقة/Level، نحتاج واحدًا من التالي:

- ملف 1080p H.264 High 8-bit قريب في معدل الإطارات والـLevel من E116؛ أو
- تقرير قدرات MediaCodec الفعلية للجهاز يظهر إن كان يوجد AVC High10 decoder يدعم Level 5.0؛ أو
- Logcat لتشغيل نسخة 1080p الفاشلة في التطبيق، خصوصًا أخطاء `MediaCodec` و`MediaCodecVideoRenderer` و`DecoderInitializationException`.

## حدود ما تم إثباته

- تم إثبات وجود علاقة قوية بين ملفات الفشل وHigh10/10-bit عبر المقارنة بين الملفات الخمسة.
- لم يُثبت بعد أن الهاتف لا يملك أي Decoder High10؛ تقارير FFmpeg لا تقرأ قدرات Android MediaCodec.
- لم يتم تعديل APK أو بناء إصدار جديد.
- مصدر PATCH242 متاح للتحليل، لكن مصدر 245 الكامل غير متوفر ضمن الملفات التي أمكن الوصول إليها في هذه الجلسة؛ لذلك لا أنسب تفاصيل PATCH242 إلى 245 دون مقارنة مصدر 245.

## مراجع تقنية

- ExoPlayer `DefaultRenderersFactory.setEnableDecoderFallback`: https://github.com/google/ExoPlayer/blob/release-v2/library/core/src/main/java/com/google/android/exoplayer2/DefaultRenderersFactory.java
- ExoPlayer `MediaCodecVideoRenderer`: https://github.com/google/ExoPlayer/blob/release-v2/library/core/src/main/java/com/google/android/exoplayer2/video/MediaCodecVideoRenderer.java
- Android `MediaCodecInfo.CodecProfileLevel.AVCProfileHigh10`: https://developer.android.com/reference/android/media/MediaCodecInfo.CodecProfileLevel#AVCProfileHigh10
- Android `MediaCodecList.findDecoderForFormat`: https://developer.android.com/reference/android/media/MediaCodecList#findDecoderForFormat(android.media.MediaFormat)
