# Application constants

# Example genome analysis ID used for demo/testing purposes
# Update this ID if you recreate the example analysis
EXAMPLE_ANALYSIS_ID = '6d7ca115-d07e-419f-9b1f-f5d133c0707b'

# AI prompt used when generating plain-text analyses for categories.
# Keep this short and explicit: request plain text paragraphs, no markdown, no headers, no lists.
# Update this text to refine the style of the AI output.
AI_PLAIN_TEXT_ANALYSIS_PROMPT = (
	"INSTRUCTION: Produce 2-4 short paragraphs of PLAIN TEXT only. Do NOT use markdown, headings, lists, tables, separators (---), or any special formatting. "
	"Do not include bullet points, numbered lists, or code blocks. Write directly in clear prose. "
	"Focus on explaining what the genetic findings mean for a non-expert, practical implications, and next steps. Do NOT provide medical advice — include a single-sentence disclaimer recommending consultation with a healthcare professional."
)
