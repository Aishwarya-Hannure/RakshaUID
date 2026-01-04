#ocr_extractor
from paddleocr import PaddleOCR
import cv2


ocr = PaddleOCR( use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False, lang='en' )

def run_ocr(image_path):
    img = cv2.imread(image_path)
    result = ocr.ocr(img)
    texts = []
    boxes = []
    scores = []

    for line in result:
        texts.append(line['rec_texts'])
        boxes.append(line['rec_boxes'])
        scores.append(line['rec_scores'])

    return {
        "rec_texts": texts,
        "rec_boxes": boxes,
        "rec_scores": scores
    }
# img = "F:\\New folder (2)\\newdatasets\\train\\real\\real_1.jpg"
# print(run_ocr_full(img))

