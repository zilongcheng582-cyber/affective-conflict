# EmotionTalk Controlled Protocol Design V1 — Frozen

Protocol and master panel (1,500 rows) are FROZEN. No inference or generation ran; science status NOT_RUN. Next step: EMOTIONTALK_MASTER_PANEL_MEDIA_FREEZE.

## Science and labels
Study A-V, A-T, V-T arbitration in both orders, compare pair structures, and test pairwise-to-T+A+V prediction. Frozen source strings: angry, disgusted, fearful, happy, neutral, sad, surprised. Official numeric correspondence only: neutral=0, happy=1, sad=2, angry=3, surprised=4, disgusted=5, fearful=6; numeric IDs are not a new ontology. y_T/y_A/y_V are evidence-side source labels, not objective truth. y_M is a source multimodal percept label, excluded from selection, readability, winner, graph, and prediction; secondary descriptive only.

## Official provenance and split
Official repo /root/autodl-tmp/affective-conflict/external/EmotionTalk, commit cb8397e226ce7c1fccee41ea21161a3f98f578e1, branch main, clean. Repo cross-check PASS in audit/EMOTIONTALK_OFFICIAL_REPO_CROSSCHECK_V1/. Four modalities have 19,250 aligned basename-stem IDs. Four label NPZs share train=15,413, val=1,908, test=1,929. Membership AVAILABLE from LABEL_NPZ; split generation rule and speaker split implementation NOT_FOUND. Do not infer rules from README or filenames. Split is not a panel filter. Descriptive panel composition: train=1190, val=158, test=152.

## Master panel
Each T/A/V pattern contributes 300: ALL_SAME, T=A!=V, T=V!=A, A=V!=T, ALL_DIFFERENT. Therefore every pair has 900 conflict and 600 consistent. Stratify by ordered T/A/V label tuple, one slot per observed tuple then proportional residual-capacity allocation using floor and largest remainder, lexical tie-break. Seed 42 shuffles IDs within tuples. See selection JSON for all allocations and IDs. Do not use split, y_M, model outputs, readability, media length/difficulty, or future outcomes. speaker_id comes directly from Text annotation JSON, never filename inference.

## Candidate design and phases
Use seven cyclic rotations plus seven reversed rotations. Each label-position cell occurs 214 or 215 times, range 1. Keep each utterance's sequence identical across arms.

Phase 1: T_ONLY/A_ONLY/V_ONLY on all rows; fixed 4,500 generations. Readable means prediction equals that modality's source label. DualReadable requires both pair modalities; TripleReadable requires all three.

Phase 2: run both pair orders only on corresponding DualReadable items. Main population is source conflict and DualReadable; consistent and DualReadable is control. Reuse Phase 1 and pair by utterance. Conditional generations: 2*N_DualReadable_AV + 2*N_DualReadable_AT + 2*N_DualReadable_VT.

Phase 3: six orders (T>A>V, T>V>A, A>T>V, A>V>T, V>T>A, V>A>T) on TripleReadable and not ALL_SAME. Conditional generations: 6*N_TripleReadable_non_ALL_SAME. Freeze graph and prediction rules before output. OTHER and PARSE_FAIL remain separate.

## Video and execution gates
All 100 sampled Fast Audit V2 MP4s contain audio. Every V input, including V_ONLY and tri-modal V, must be DERIVED_SILENT_VIDEO. Pair arms use separate WAV plus silent video. Separate audio plus original AV MP4 is forbidden. Official visual pipeline uses face-frame arrays; no silent-video derivation was found. Derive none now; later derive only these 1,500, stream-copy only, no automatic re-encode.

Gate C covers unimodal arms, P covers all pairs and both orders, T covers six tri-modal orders. Gates are technical only. OOM is TECHNICAL_MISSINGNESS: no automatic quality reduction, alternate preprocessing retry, or outcome-based skipping. Pixel budget waits for post-derivation resource calibration.

EMOTIONTALK_CONTROLLED_PROTOCOL_V1_STATUS=FROZEN  
EMOTIONTALK_MASTER_PANEL_V1_STATUS=FROZEN  
EMOTIONTALK_SCIENCE_STATUS=NOT_RUN  
MODEL_INFERENCE_RUN=FALSE  
EMOTIONTALK_MEDIA_STATUS=MASTER_PANEL_SELECTED_SILENT_VIDEO_NOT_YET_DERIVED  
NEXT_STEP=EMOTIONTALK_MASTER_PANEL_MEDIA_FREEZE
