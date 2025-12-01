import numpy as np
from django.db import connection
import json


# 1) 임베딩 생성 (AI 서버 붙기 전까지 사용)
def generate_fake_embedding():
     return np.random.rand(768).tolist()


# 2) Supabase PostgreSQL pgvector 유사도 검색
def vector_similarity(vec, top_k=3):
     db_engine = connection.settings_dict['ENGINE']

     if "sqlite" in db_engine:
          return []

     vec_str = json.dumps(vec)

     with connection.cursor() as cursor:
          cursor.execute(
               """
               SELECT
                    atc_id,
                    fd_sn,
                    item_name,
                    ai_generated_desc,
                    police_image_url,
                    COALESCE(1 - (vlm_embedding <=> %s), 0.0) AS similarity
               FROM police_found_item
               WHERE vlm_embedding IS NOT NULL
               ORDER BY vlm_embedding <=> %s ASC
               LIMIT %s;
               """,
               [vec_str, vec_str, top_k],
          )
          rows = cursor.fetchall()

     return [
          {
               "atc_id": row[0],
               "fd_sn": row[1],
               "item_name": row[2],
               "ai_generated_desc": row[3],
               "police_image_url": row[4],
               "similarity_score": float(row[5]),
               "detail_link": f"https://www.lost112.go.kr/find/findDetail.do?atcId={row[0]}&fdSn={row[1]}",
          }
          for row in rows
     ]