# Datasets and external inputs

 No raw media, NPZ, parquet, dataset archives or model weights are distributed. Obtain data from original providers under their terms; retained dataset identity metadata does not grant access.

 | Dataset | Source identity | Required placement below AF_DATA_ROOT | Required inputs / frozen boundary |
 |---|---|---|---|
 | EmotionTalk | Official source commit cb8397e226ce7c1fccee41ea21161a3f98f578e1 | data/EmotionTalk/extracted/{Text,Audio,Video,Multimodal}/json; Audio/wav; Multimodal/mp4; external/EmotionTalk/EmotionTalk/dataset/mm-process | 19250 records per annotation modality; txt_label/audio_label/video_label/mm_label.npz; exact1500 panel and media definitions in manifests/emotiontalk |
 | MCR-Bench | Released SER.json SHA256 58aff644175739b142f46ea9f47c32f9230f3cf7fc033dfdd4e8750ee3e6b880 | data/MCR-Bench/MCR-Bench/SER/SER.json plus relative raw audio | 1000 native rows; raw duplicate/source-label mapping →909 canonical arbitration records; use frozen current artifact, not old candidate ordering |
 | LISTEN | Dataset revision f6397b5bfedd85ae41b80dac13e95bb55adf0a35; official repo commit32966584488bd3b3c67a150bd55f1f18ca09ef76 | data/LISTEN/data/train-*.parquet; audit/QWEN25_LISTEN_NATIVE_V3/input_audio/{SHA256}.wav | Three train shards, 11507 source records; replay complete nine-condition stream with17190 preceding valid shuffles before1149 final3A/3B/3C slots; 768 distinct scientific IDs; Python3.12/PYTHONHASHSEED42 |
 | CA-MER / MER2023 | MER2023 revision9d7a285654c722abd30d3c67b6ade477f1a75e16; pinned official annotation blobs | data/CA-MER; audit/QWEN25_CAMER_NATIVE_V1/official_annotation; authorized extracted MER2023 media paths per explicit mapping | audio-aligned/video-aligned/consistent, 500 each; 1500 exact IDs; canonical physical mapping and separately hashed derived audio/silent video |

 LISTEN raw shard SHA256s: f6ceaeb135f8338346ad6ce105cb48ed4863fb92e87b822964372280f5eb6475; f721d9528f07dd21052443f3a356ac01a2d0949cb7e5056fc3e7e5bd2e6df811; 6d102f09616fee959ab52009618b5ecf79fd7c6e19f835937ac478dfc0ef3470. Embedded audio must first be extracted byte-identically to its content-addressed WAV cache; replay validates that cache.

 CA-MER pinned annotation SHA256s: audio-aligned8e9ab161ca4a9c898a60f342ae47742a4eba6b7597df3b31863fb511171347de; video-alignedae54fc12b1fdc5e36a76f95c230809a834c6a5831172dfef1745c72e5d8504ff; consistentcc9ae34a9f1a0a6580f64472350f76af3bf4d2b5dc749cae29f3560c9b908a57. Preserve16 source-local labels; no synonym/ontology mapping is permitted.

 Model/processor: obtain Qwen/Qwen2.5-Omni-7B at immutable commit ae9e1690543ffd5c0221dc27f79834d0294cba00 and verify every frozen model_files.csv/processor_files.csv digest. This repository contains repo ID, immutable commit and content identity only; no weights, tokenizer/processor cache or HF download cache is shipped.

 Required frozen derived artifacts are shipped where size permits: source candidate sequences, exact target assignment, source model/scalers, scientific protocols, task manifests, mainline joint outcomes, EmotionTalk source measurement table and trimodal plan. Large full inference records are external with hash/count catalogs. Absolute paths retained inside byte-identical frozen provenance are metadata and are resolved in memory by configured relocation; they are not hardcoded source dependencies.
