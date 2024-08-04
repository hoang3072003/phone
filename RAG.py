import os
# from dotenv import load_dotenv
import pymongo
from sentence_transformers import SentenceTransformer

embedding_model = SentenceTransformer('keepitreal/vietnamese-sbert')

def get_mongo_client(mongo_uri):
    """Establish connection to the MongoDB."""
    try:
        # Kết nối tới MongoDB sử dụng URI
        client = pymongo.MongoClient(
            mongo_uri, appname="devrel.content.python")
        print("Connection to MongoDB successful")
        return client
    except pymongo.errors.ConnectionFailure as e:
        print(f"Connection failed: {e}")
        return None
# client = get_mongo_client(os.environ["MONGODB_URI"])
client = get_mongo_client("mongodb+srv://nguyenducphuchoanghust:S3wIZkZrLbLSZPJO@clusterhoangha.ppebs8w.mongodb.net/")


def get_embedding(text: str) -> list[float]:
    if not text.strip():
        print("Attempted to get embedding for empty text.")
        return []

    embedding = embedding_model.encode(text.replace(
        '###', '').replace('\n', '').replace('<br>', ''))

    return embedding.tolist()

class RAG:
    def __init__(self, db_name="DatabaseHoangHa", collection_name="HoangHaphoneembed"):
        if not "mongodb+srv://nguyenducphuchoanghust:S3wIZkZrLbLSZPJO@clusterhoangha.ppebs8w.mongodb.net/":
            raise ValueError("MongoDB URI is missing")
        self.client = client
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def vector_search(self, user_query, collection, num_candidates=100, k=4):
        """
        Lấy ra các vector gần nhất với vector của user_query từ collection.
        Args:
            user_query (str): Câu truy vấn của người dùng.
            collection (pymongo.collection.Collection): Collection trong MongoDB.
            num_candidates (int): Số lượng vector ứng viên.
            k (int): Số lượng vector gần nhất cần lấy ra.
        Returns:
            list: Danh sách các vector gần nhất với vector của user_query.
        """

        # Generate embedding for the user query
        query_embedding = get_embedding(user_query)

        if query_embedding is None:
            return "Invalid query or embedding generation failed."

        # Định nghĩa các stage trong pipeline
        vector_search_stage = {
            "$vectorSearch": {
                "index": "vector_index",
                "queryVector": query_embedding,
                "path": "embedding",
                "numCandidates": num_candidates,  # Số lượng vector ứng viên.
                "limit": k  # Trả về k vector gần nhất.
            }
        }

        unset_stage = {
            # Loại bỏ trường embedding khỏi kết quả trả về.
            "$unset": "embedding"
        }

        project_stage = {
            "$project": {
                "_id": 0,  # Exclude the _id field
                "name": 1,  # Include the Phone field
                "price": 1,  # Include the Description field
                'specs_special': 1,  # Include the specs field
                'product_promotion': 1,
                'colors': 1,
                "score": {
                    "$meta": "vectorSearchScore"  # Include the search score
                }
            }
        }

        # Xây dựng pipeline
        pipeline = [vector_search_stage, unset_stage, project_stage]

        # Thực thi pipeline
        results = collection.aggregate(pipeline)
        return list(results)
    def get_search_result(self, query, num_candidates=100, k=4, combine_query=True):
        '''
        Lấy kết quả tìm kiếm từ vector search và trả về dưới dạng chuỗi.
        Args:
            query (str): Câu truy vấn của người dùng.
            num_candidates (int): Số lượng vector ứng viên.
            k (int): Số lượng vector gần nhất cần lấy ra.
            combine_query (bool): Kết hợp câu truy vấn với kết quả tìm kiếm hay không.
        Returns:
            str: Kết quả tìm kiếm dưới dạng chuỗi.
        '''

        def get_infomation(text, prompt):
            if isinstance(text, int):
                text = str(text)
            text = text.replace('\n', '.')
            if text:
                return f"{prompt} {text}.\n"
            else:
                return ""

        # Lấy vector database từ vector search
        db_information = self.vector_search(
            query, self.collection, num_candidates, k)

        search_result = ""

        # Duyệt qua kết quả trả về từ vector search và thêm vào search_result
        for i, result in enumerate(db_information):
            name = result.get('name', 'N/A')
            product_promotion = result.get('product_promotion', 'N/A')
            specs_special = result.get('specs_special', 'N/A')
            price = result.get('price', 'N/A') if result.get(
                'price', 'N/A') else 'Liên hệ để trao đổi thêm'
            colors = result.get('colors', 'N/A')

            search_result += f"Sản phẩm thứ {i+1}: \n"
            search_result += get_infomation(name, "Tên sản phẩm:")
            search_result += get_infomation(product_promotion,
                                            "Ưu đãi:")
            search_result += get_infomation(specs_special,
                                            "Chi tiết sản phẩm:")
            search_result += get_infomation(price, "Giá tiền:")
            search_result += get_infomation(colors,
                                            "Các màu điện thoại:")
        if not combine_query:
            return search_result
        else:
            prompt_query = query + ". " + \
                "Hãy trả lời bằng Tiếng Việt dựa trên thông tin các sản phẩm cửa hàng có như sau (Nếu không có thông tin thì hãy đề xuất sản phẩm khác ):"
            return f"Query: {prompt_query} \n {search_result}.".replace('<br>', '')
      


