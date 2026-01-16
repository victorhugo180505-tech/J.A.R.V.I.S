import base64
import os
import tempfile

import azure.cognitiveservices.speech as speechsdk


def synthesize_tts_with_visemes(
    text: str,
    *,
    key: str,
    region: str,
    voice: str = "es-MX-DaliaNeural",
):
    text = (text or "").strip()
    if not text:
        return "", []

    speech_config = speechsdk.SpeechConfig(subscription=key, region=region)
    speech_config.speech_synthesis_voice_name = voice
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm
    )

    # ✅ salida a archivo temporal (evita tema de default speaker)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp_path = tmp.name
    tmp.close()

    audio_config = speechsdk.audio.AudioOutputConfig(filename=tmp_path)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    visemes = []

    def on_viseme(evt: speechsdk.SpeechSynthesisVisemeEventArgs):
        visemes.append({
            "t": int(evt.audio_offset / 10_000),  # 100ns -> ms
            "id": int(evt.viseme_id),
        })

    synthesizer.viseme_received.connect(on_viseme)

    result = synthesizer.speak_text_async(text).get()

    # ✅ Diagnóstico correcto de cancelación (API real)
    if result.reason == speechsdk.ResultReason.Canceled:
        try:
            c = speechsdk.SpeechSynthesisCancellationDetails.from_result(result)
            reason = getattr(c, "reason", None)
            code = getattr(c, "error_code", None)
            details = getattr(c, "error_details", None)
        except Exception as e:
            reason = None
            code = None
            details = f"(No pude leer CancellationDetails: {repr(e)})"

        # limpia tmp
        try:
            os.remove(tmp_path)
        except Exception:
            pass

        raise RuntimeError(
            "TTS canceled: "
            f"reason={reason} "
            f"error_code={code} "
            f"error_details={details}"
        )

    if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        raise RuntimeError(f"TTS failed: {result.reason}")

    # ✅ leer WAV
    try:
        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass

    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    return audio_b64, visemes
