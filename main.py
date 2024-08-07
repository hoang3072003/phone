import os
import streamlit as st
from function_calling import search_phone_by_rules, search_phone_info_by_name, model, available_tools1
from query_process import classification_query
import google.generativeai as genai

# Streamlit app title
st.set_page_config(page_title="Hedspi Phone Store", page_icon=":iphone:")
st.title("Hedspi Phone Store Chatbot")

# Initialize model and session state
if 'chat' not in st.session_state:
    st.session_state.chat = model.start_chat(history=[])
if 'messages' not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "Bạn là một nhân viên bán hàng điện thoại trong cửa hàng điện thoại di động Hedspi. Nhiệm vụ của bạn là giúp khách hàng tìm chiếc điện thoại tốt nhất phù hợp với nhu cầu của họ."}
    ]
if 'query_list' not in st.session_state:
    st.session_state.query_list = []

col1, col2 = st.columns([3, 7])  # chia tỉ lệ 2 cột 25% và 75%
with col1:
    if st.button("Làm mới cuộc trò chuyện"):
        st.session_state.messages = [
            {"role": "system", "content": "Bạn là một nhân viên bán hàng điện thoại trong cửa hàng điện thoại di động Hedspi. Nhiệm vụ của bạn là giúp khách hàng tìm chiếc điện thoại tốt nhất phù hợp với nhu cầu của họ."}
        ]
        st.session_state.query_list = []
        st.session_state.chat = model.start_chat(history=[])
        st.experimental_rerun()  # chạy lại chatbot

with col2:
    if st.button("Đến website bán hàng"):
        website_url = os.environ.get('WEBSITE', 'https://www.example.com')
        st.write(f'<a href={website_url} target="_blank">Bấm vào để quay lại cửa hàng</a>', unsafe_allow_html=True)

# In lịch sử chat
for i, message in enumerate(st.session_state.messages):
    if message["role"] == "user":
        with st.chat_message(message["role"]):
            if i-1 < len(st.session_state.query_list):
                st.write(st.session_state.query_list[i-1])
            else:
                st.write(message["content"])
    elif message["role"] != "system":
        with st.chat_message(message["role"]):
            st.write(message["content"])

# Khi đầu vào từ người dùng
if prompt := st.chat_input("Bạn cần chúng tôi hỗ trợ gì?"):
    # Hiển thị query
    with st.chat_message("user"):
        st.session_state.query_list.append(prompt)
        st.markdown(prompt)
    
    st.session_state.messages.append({"role": "user", "content": prompt})

    is_needRAG = True   
    # classification_query([prompt])

    if is_needRAG:
        response = st.session_state.chat.send_message(prompt)
        while True:
            # Tạo dictionary để lưu trữ kết quả từ các hàm
            responses = {}

            # Xử lý từng phần của phản hồi từ chatbot
            for part in response.parts:
                print(1)
                # Kiểm tra xem phần phản hồi có chứa yêu cầu gọi hàm hay không
                if fn := part.function_call:
                    function_name = fn.name
                    function_args = ", ".join(f"{key}={val}" for key, val in fn.args.items())
                    print(function_name,function_args)
                    # Lấy hàm tương ứng từ available_tools
                    function_to_call = available_tools1[function_name]

                    # Phân tích chuỗi function_args thành dictionary
                    function_args_dict = {}
                    for item in function_args.split(", "):
                        key, value = item.split("=")
                        function_args_dict[key.strip()] = value.strip()

                    # Gọi hàm và lưu kết quả vào dictionary responses
                    function_response = function_to_call(**function_args_dict)
                    responses[function_name] = function_response
                else:
                    print("no functioncalling")
            # Nếu có kết quả từ các hàm
            if responses:
                # Tạo danh sách các phần phản hồi mới, bao gồm kết quả từ các hàm
                response_parts = [
                    genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=fn, response={"result": val}
                        )
                    )
                    for fn, val in responses.items()
                ]
                # Gửi phản hồi mới (bao gồm kết quả từ các hàm) cho chatbot
                response = st.session_state.chat.send_message(response_parts)
                # response = model.generate_content(response_parts)
            else:
                break
        with st.chat_message("assistant"):
            st.write(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
    
    
    # else:
    #     response = st.session_state.chat.send_message(prompt)
    # # In ra phản hồi cuối cùng từ chatbot
    # with st.chat_message("assistant"):
    #     st.write(response.text)
    # st.session_state.messages.append({"role": "assistant", "content": response.text})