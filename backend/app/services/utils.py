import re

# 1. SHARED ABBREVIATIONS
# Used by Transformer (for sentence splitting lookbehind) 
# and AudioEngine (for speech normalization)
COMMON_ABBREVIATIONS = {
    r'\bNo\.': 'Number ',
    r'\bSr\.': 'Serial ',
    r'\bRef\.': 'Reference ',
    r'\bDr\.': 'Doctor ',
    r'\bMr\.': 'Mister ',
    r'\bDept\.': 'Department ',
    r'\bOps\.': 'Operations ',
    r'\bGovt\.': 'Government ',
    r'\bApprox\.': 'Approximately ',
    r'\bBatch No\.': 'Batch Number '
}

# 2. FILLER WORDS
# Introductory words to strip from bullets for punchy training
FILLER_WORDS_REGEX = r'^(Therefore|Additionally|Furthermore|In addition|Generally|Notably|It should be noted that|Please note that|Observe that)\s*,?\s*'

# 3. DOCUMENT NOISE
# Layout artifacts to ignore during extraction
DOCUMENT_NOISE_PATTERNS = [
    r'Page\s+\d+', 
    r'\d+\s+of\s+\d+', 
    r'Ref\.\s+SOP\s+No\.', 
    r'^\d+$', 
    r'Confidential', 
    r'Property of',
    r'INVESTIGATION REPORT', 
    r'DEVIATION No\.'
]

def normalize_for_speech(text: str) -> str:
    """Normalizes symbols and abbreviations into spoken words for TTS."""
    if not text: return ""
        
    # 1. Expand Abbreviations
    for pattern, spoken in COMMON_ABBREVIATIONS.items():
        text = re.sub(pattern, spoken, text, flags=re.IGNORECASE)

    # 2. Standard symbol replacements
    symbols = {
        '→': ' leads to ',
        '%': ' percent ',
        '&': ' and ',
        '@': ' at ',
        '#': ' number ',
        '+': ' plus ',
        '=': ' equals ',
        '>': ' greater than ',
        '<': ' less than ',
        '/': ' or ',
        '|': ' or ',
        '~': ' approximately '
    }
    for symbol, spoken in symbols.items():
        text = text.replace(symbol, spoken)

    # 3. Emphasis markers
    text = text.replace("Important:", "Important point: ")
    text = text.replace("Note:", "Please note: ")
    text = text.replace("NB:", "Note well: ")
    
    return re.sub(r'\s+', ' ', text).strip()

def clean_leading_markers(text: str) -> str:
    """Remove leading bullet markers like *, -, or . from a string."""
    if not text: return ""
    return re.sub(r'^[ \t]*[\*\u2022\-\.]+[ \t]*', '', text).strip()
