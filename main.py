import cv2
import numpy as np


def detect_kelp_disease(image_path):
    """
    通过颜色检测海带苗的病变和健康部分。
    """
    # 1. 读取图片
    image = cv2.imread(image_path)
    if image is None:
        print(f"错误：无法读取图片 '{image_path}'，请检查路径是否正确。")
        return

    # 2. 调整图片大小以适应屏幕显示
    # 定义一个用于显示的最大高度，例如 800 像素
    max_display_height = 800
    original_height, original_width = image.shape[:2]

    # 只有当图片实际高度大于我们设定的最大高度时，才进行缩放
    if original_height > max_display_height:
        # 计算缩放比例
        scale_factor = max_display_height / original_height
        # 计算新的宽度和高度
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)
        # 使用 cv2.resize 进行缩放
        image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        print(f"图片尺寸已从 {original_width}x{original_height} 调整为 {new_width}x{new_height} 以便显示。")

    # 3. 将图片从 BGR 转换到 HSV 颜色空间
    # 所有后续操作都将在这个调整过尺寸的图片上进行，这样速度更快
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # 4. 定义颜色范围 (HSV)
    # !!! 注意：这仍然是最关键的一步，您需要使用上一节提供的HSV调节工具来找到最适合您图片的值 !!!
    # 并将找到的值填入下面

    # 示例：浅绿色（病变部分）的HSV范围
    # light_green_lower = np.array([30, 25, 12])
    # light_green_upper = np.array([108, 234, 136])
    light_green_lower = np.array([29, 50, 51])
    light_green_upper = np.array([105, 211, 178])
    # 示例：深绿色（健康部分）的HSV范围
    # dark_green_lower = np.array([0, 30, 40])
    # dark_green_upper = np.array([31, 254, 130])
    dark_green_lower = np.array([0, 0, 0])
    dark_green_upper = np.array([29, 254, 208])

    # 5. 根据颜色范围创建掩码（Mask）
    diseased_mask = cv2.inRange(hsv_image, light_green_lower, light_green_upper)
    healthy_mask = cv2.inRange(hsv_image, dark_green_lower, dark_green_upper)

    # 可选：形态学操作，去除噪点
    kernel = np.ones((5, 5), np.uint8)
    diseased_mask = cv2.morphologyEx(diseased_mask, cv2.MORPH_OPEN, kernel)
    diseased_mask = cv2.morphologyEx(diseased_mask, cv2.MORPH_CLOSE, kernel)

    # 6. 将掩码应用到原始图像上
    diseased_result = cv2.bitwise_and(image, image, mask=diseased_mask)
    healthy_result = cv2.bitwise_and(image, image, mask=healthy_mask)

    # 7. 在原始图像的副本上框出病变区域
    output_image = image.copy()
    contours, _ = cv2.findContours(diseased_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(output_image, contours, -1, (0, 0, 255), 2)  # 用2像素粗的红线框出

    # 8. 显示所有结果窗口
    # cv2.WINDOW_NORMAL 参数允许用户手动调整窗口大小
    cv2.namedWindow('Original Image', cv2.WINDOW_NORMAL)
    cv2.imshow('Original Image', image)

    cv2.namedWindow('Diseased Part (Light Green)', cv2.WINDOW_NORMAL)
    cv2.imshow('Diseased Part (Light Green)', diseased_result)

    cv2.namedWindow('Healthy Part (Dark Green)', cv2.WINDOW_NORMAL)
    cv2.imshow('Healthy Part (Dark Green)', healthy_result)

    cv2.namedWindow('Detected Disease Outlined', cv2.WINDOW_NORMAL)
    cv2.imshow('Detected Disease Outlined', output_image)

    # 等待按键，然后关闭所有窗口
    cv2.waitKey(0)
    cv2.destroyAllWindows()


# --- 使用示例 ---
if __name__ == '__main__':
    # 将 'path/to/your/kelp_image.jpg' 替换成你的图片路径
    image_file = r'E:\pythonpro\detect_kelp_disease\kelp_picture\disease\6-1.JPG'
    detect_kelp_disease(image_file)