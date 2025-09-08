#!/usr/bin/env python3
"""
修復圖片顯示 - 支援點擊放大
"""

def create_image_display_patch():
    """
    修正 main_app.py 和 ui_helpers.py 中的圖片顯示
    """
    
    # main_app.py 的圖片顯示代碼
    main_app_code = '''                images = full_response_data.get("images") or []
                if images:
                    unique_images = create_unique_images_list(images)
                    if unique_images:
                        st.markdown("**📸 相關圖片：**")
                        
                        # 顯示可點擊放大的圖片
                        for i, img_path in enumerate(unique_images[:3]):
                            try:
                                # 使用expander提供放大功能
                                with st.expander(f"🖼️ 圖片 {i+1} - {os.path.basename(img_path)}", expanded=False):
                                    st.image(img_path, use_column_width=True)
                            except Exception as e:
                                st.error(f"無法顯示圖片 {i+1}: {e}")'''
                                
    # ui_helpers.py 的圖片顯示代碼  
    ui_helpers_code = '''                    # 顯示相關圖片
                    st.markdown("**📸 相關圖片：**")
                    
                    # 顯示可點擊放大的圖片
                    for i, img_path in enumerate(unique_images[:3]):
                        try:
                            # 使用expander提供放大功能  
                            with st.expander(f"🖼️ 圖片 {i+1} - {os.path.basename(img_path)}", expanded=False):
                                st.image(img_path, use_column_width=True)
                        except Exception as e:
                            st.error(f"無法顯示圖片 {i+1}: {e}")'''
    
    print("修正代碼已準備，需要手動替換文件中的圖片顯示邏輯")
    print("\n=== main_app.py 替換代碼 ===")
    print(main_app_code)
    print("\n=== ui_helpers.py 替換代碼 ===")
    print(ui_helpers_code)

if __name__ == "__main__":
    create_image_display_patch()
