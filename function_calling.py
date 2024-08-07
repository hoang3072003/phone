# -*- coding: utf-8 -*-
from db import phones_data
from difflib import SequenceMatcher
import json
import google.generativeai as genai
import os
from RAG import RAG
from dotenv import load_dotenv
load_dotenv()
def compare(a, b):
    a = a.lower()
    b = b.lower()
    if SequenceMatcher(None, a, b).ratio() > 0.7:  
        return b
    elif a in b:
        return b
    else:
        return None  

def search_phone_by_rules(
    name: str ="pass",
    price: str = "pass",
    colors: str = "pass",
    sort_by: str = "pass",
    sort_rule: str = "pass",
    choose_range: str = "pass",
) -> str:
    """
    Lọc danh sách điện thoại theo các tiêu chí nhất định và cung cấp thông tin cơ bản về các mẫu điện thoại phù hợp. Hàm này giúp bạn tìm kiếm và sắp xếp các mẫu điện thoại theo nhu cầu cụ thể của người dùng.
    Args:
        name: Danh sách tên điện thoại hoặc từ khóa tên điện thoại mà bạn muốn tìm kiếm. Đặt name = "pass" nếu không muốn sử dụng bộ lọc này.
            Ví dụ:
                - "Samsung Galaxy Z Fold6; iphone 15 promax".
                - "Samsung Galaxy; iPhone".
        price: Danh sách giá trị giá của điện thoại mà bạn muốn lọc. Đặt price = "pass" nếu không muốn sử dụng bộ lọc này.
            Ví dụ:
                - "5000000; 10000000" (đơn vị VNĐ).
                - "0;10000000" tương ứng với nhỏ hơn 10 triệu (đơn vị VNĐ)
                - "10000000;1000000000000" tương ứng với lớn hơn 10 triệu (đơn vị VNĐ)
        colors: Danh sách màu sắc của điện thoại mà bạn muốn tìm kiếm. Đặt colors = "pass" nếu không sử dụng bộ lọc này.
            Ví dụ:
                - "màu đỏ; màu đen".
        sort_by: Tiêu chí sắp xếp mà bạn muốn thực hiện. Các tiêu chí hợp lệ bao gồm (price). Đặt sort_by = "pass" nếu không sử dụng tính năng sắp xếp.
            Ví dụ:
                - "price".
        sort_rule: Quy tắc sắp xếp mà bạn muốn áp dụng. Các quy tắc sắp xếp hợp lệ bao gồm (increase, decrease). Đặt sort_rule = "pass" nếu không sử dụng tính năng sắp xếp.
            Ví dụ:
                - "decrease".
        choose_range: Khoảng giá trị mà bạn muốn lấy sau khi sắp xếp. Đặt choose_range = "pass" nếu không sử dụng tính năng này.
            Ví dụ:
                - "1; 5" (lấy 5 sản phẩm đầu tiên).

    Returns:
        Chuỗi JSON chứa danh sách điện thoại phù hợp với yêu cầu của bạn.
    """
    # json_file_path = "df_hoanghamobile.json"
    # with open(json_file_path, "r", encoding="utf-8") as f:
    #     phones = json.load(f)["phones"]
    phones = phones_data["phones"]
    if name != "pass":
        names = [n.strip().lower() for n in name.split(";")]
        phones1 = []
        for a in names:
            phones1 += [p for p in phones if p["name"].lower()==compare(a,p['name'])]
    else:
        phones1 = phones
    if colors != "pass":
        colorss = [c.strip().lower() for c in colors.split(";")]
        phones2 = []
        for c in colorss:
            phones2+=[p for p in phones1 if compare(c.replace('màu','').replace('mau','').strip(),p['colors']) is not None]

    else:
        phones2 = phones1
    if price != "pass":
        prices = [int(p.strip()) for p in price.split(";")]
        phones2 = [p for p in phones2 if int(p["price"]) >= prices[0] and int(p["price"]) <= prices[1]]

    if sort_by != "pass":
        if sort_by.lower() == "price":
            phones2 = sorted(
                phones2,
                key=lambda x: int(x["price"]),
                reverse=sort_rule.lower() == "decrease",
            )
    if choose_range != "pass":
        start, end = [int(float(c.strip())) for c in choose_range.split(";")]
        phones2 = phones2[start - 1 : end]

    return json.dumps({"phones": phones2}, ensure_ascii=False, indent=4)

def search_phone_info_by_name(name: str) -> str:
    """
    Cung cấp những thông tin chi tiết về các sản phẩm điện thoại có tên giống với tên bạn cần tìm, bao gồm giá cả, ưu đãi, khuyến mãi, chi tiết sản phẩm, màu sắc, và các thông tin đặc biệt khác.

    Args:
        name: Tên của sản phẩm điện thoại bạn cần tìm hiểu.
             Ví dụ:
                - "Samsung Galaxy Z Fold6", "iPhone 14 Pro"
    Returns:
        Chuỗi JSON chứa thông tin chi tiết về các sản phẩm điện thoại liên quan.
    """
    # rag_instance =  RAG()
    # results = rag_instance.get_search_result(name)
    # formatted_results = []
    # for doc in results:
    #     content = doc["name"] + " " + str(doc["price"]) + " " + doc["specs_special"] + " " + doc["product_promotion"] + " " + doc["colors"]
    #     formatted_results.append({"content": content})
    # docs_string = json.dumps(formatted_results, ensure_ascii=False, indent=4)
    # return docs_string
    rag_instance =  RAG()
    result_string = rag_instance.get_search_result(name)
    result_string = result_string.split("\n")
    # formatted_results = []
    # results = result_string.split("Sản phẩm thứ")[1:]  
    # for result in results:
    #     parts = result.split("\n")
    #     content = {}
    #     for part in parts:
    #         if "Tên sản phẩm:" in part:
    #             content["name"] = part.split("Tên sản phẩm:")[1].strip()
    #         elif "Ưu đãi:" in part:
    #             content["product_promotion"] = part.split("Ưu đãi:")[1].strip()
    #         elif "Chi tiết sản phẩm:" in part:
    #             content["specs_special"] = part.split("Chi tiết sản phẩm:")[1].strip()
    #         elif "Giá tiền:" in part:
    #             content["price"] = part.split("Giá tiền:")[1].strip()
    #         elif "Các màu điện thoại:" in part:
    #             colors = part.split("Các màu điện thoại:")[1].strip()
    #             colors_cleaned = colors.split(',')
    #             colors_cleaned = [color.strip() for color in colors_cleaned if color]
    #             content["colors"] = ", ".join(colors_cleaned)
    #     formatted_results.append(content)

    docs_string = json.dumps(result_string, ensure_ascii=False, indent=4)
    return docs_string

tools1 = [
    # search_phone_info_by_name,
    search_phone_by_rules,
]

available_tools1 = {
    # "search_phone_info_by_name": search_phone_info_by_name,
    "search_phone_by_rules": search_phone_by_rules,
}
# api_key = os.getenv("API_KEY")
# genai.configure(api_key=api_key)

genai.configure(api_key="AIzaSyDCSICwl5CCqffQnW13XkaG6E3f5--8jus")  

system_instruction = """
    Bạn là một trợ lý ảo thông minh, làm nhiệm vụ bán hàng cho một cửa hàng điện thoại. 
    Bạn có khả năng truy xuất thông tin từ cơ sở dữ liệu để trả lời câu hỏi của người dùng một cách chính xác và hiệu quả.
    Hãy nhớ:
    - Luôn luôn sử dụng các công cụ được cung cấp để tìm kiếm thông tin trước khi đưa ra câu trả lời.
    - Trả lời một cách ngắn gọn, dễ hiểu.
    - Không tự ý bịa đặt thông tin.
    - Chú ý tránh lỗi mã hóa đầu vào khi sử dụng các công cụ được cung cấp. LUÔN LUÔN dùng string tiếng việt mã utf 8.
    Lưu ý: Bạn phải sử dụng phối hợp các công cụ được cung cấp để đưa ra câu trả lời cho người dùng, ví dụ, với yêu cầu 'cung cấp 3 điện thoại samsung có giá đắt nhất'
    bạn sẽ tìm danh sách những điện thoại phù hợp bằng tool 'search_phone_by_rules'.
"""  
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    tools=tools1,
    system_instruction=system_instruction
)