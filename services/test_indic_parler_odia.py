"""
Standalone test for ai4bharat/indic-parler-tts Odia synthesis.

Run this directly (NOT through Streamlit) to check, before touching any
app code:
  1. Does the model download and load successfully?
  2. How long does inference actually take on your machine?
  3. Does the resulting audio sound right when you play it?

    python test_indic_parler_odia.py

First install (this pulls PyTorch + transformers + the model code):
    pip install git+https://github.com/huggingface/parler-tts.git

Expect the first run to take a while — it downloads model weights from
Hugging Face. Subsequent runs reuse the local cache and are faster to
start (though inference time itself won't change).
"""

import time

print("Loading model (first run downloads weights — this may take a while)...")
t0 = time.time()

import torch
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer
import soundfile as sf

device = "cuda:0" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

model = ParlerTTSForConditionalGeneration.from_pretrained(
    "ai4bharat/indic-parler-tts-pretrained"
).to(device)
tokenizer = AutoTokenizer.from_pretrained("ai4bharat/indic-parler-tts-pretrained")
description_tokenizer = AutoTokenizer.from_pretrained(model.config.text_encoder._name_or_path)

print(f"Model loaded in {time.time() - t0:.1f}s\n")

# A short, real Odia phrase — "Welcome, how can I help you?"
odia_text = "ସ୍ୱାଗତମ, ମୁଁ ଆପଣଙ୍କୁ କିପରି ସାହାଯ୍ୟ କରିପାରିବି?"
# Debjani is one of the model's two officially recommended Odia speakers
# (the other is Manas) — naming a speaker explicitly gives more
# consistent, higher-quality output per the model's own documentation.
voice_description = ("Debjani speaks with a clear voice in a close-sounding "
                      "recording of very high quality, at a normal pace.")

print("Synthesizing...")
t1 = time.time()

input_ids = description_tokenizer(voice_description, return_tensors="pt").to(device)
prompt_input_ids = tokenizer(odia_text, return_tensors="pt").to(device)

generation = model.generate(
    input_ids=input_ids.input_ids,
    attention_mask=input_ids.attention_mask,
    prompt_input_ids=prompt_input_ids.input_ids,
    prompt_attention_mask=prompt_input_ids.attention_mask,
)
audio_arr = generation.cpu().numpy().squeeze()

elapsed = time.time() - t1
print(f"Synthesis took {elapsed:.1f}s for {len(odia_text)} characters "
      f"({elapsed / len(odia_text):.2f}s/char)")

sf.write("odia_parler_test_output.wav", audio_arr, model.config.sampling_rate)
print("\nSaved to odia_parler_test_output.wav — play this file and listen.")
print("\nIf it sounds like clear, correct Odia speech: this is viable, "
      "but factor the per-message synthesis time above into whether it's "
      "fast enough for a live chat demo.")
print("If it sounds garbled, wrong-language, or robotic: this model "
      "isn't a good fit — fall back to text-only Odia (Option 2 from "
      "before) rather than shipping bad audio.")