# MuRIL / Colab (not in the laptop demo)

The P_117 spec listed MuRIL or IndicBERT fine-tunes. This repo ships **sklearn TF-IDF** so `git clone` runs on an 8 GB intern laptop without downloading 400MB+ weights.

To add MuRIL later (Colab GPU):

1. Load `data/tickets.csv`
2. Encode with `google/muril-base-cased`
3. Train two linear heads (department, urgency)
4. Export ONNX or small adapters into `models/`
5. Swap `ticketroute/predict.py` `load_models()`

Do not check large `.bin` files into GitHub.
