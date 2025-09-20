<template>
  <div class="kelp-detector">
    <header>
      <h1>海带病害图像分割与分析</h1>
      <p v-if="!opencvReady" class="loading-status">
        正在加载图像处理引擎 (OpenCV.js)，请稍候...
      </p>
      <p v-else class="ready-status">
        引擎加载完毕，请上传图片进行分析。
      </p>
    </header>

    <div class="upload-section">
      <div v-if="!originalImageUrl" class="drop-area" @dragover.prevent @drop.prevent="handleDrop">
        <input type="file" id="fileInput" @change="handleFileChange" accept="image/png, image/jpeg, image/jpg" hidden>
        <label for="fileInput" class="upload-button">上传文件</label>
        <span>或拖拽到此处</span>
        <small>支持 PNG, JPG, JPEG 格式</small>
      </div>
      <div v-else class="re-upload-section">
         <button @click="reset" class="re-upload-button">重新上传</button>
      </div>
    </div>

    <div v-if="isProcessing" class="processing-status">
      <p>正在处理图片，请稍候...</p>
      <div class="spinner"></div>
    </div>

    <div v-if="originalImageUrl" class="results-grid">
      <div class="image-card">
        <h3>原始图片</h3>
        <img :src="originalImageUrl" id="originalImage" alt="Original Kelp Image" @load="onImageLoad"/>
      </div>
      <div class="image-card">
        <h3>分割后的图片</h3>
        <canvas id="outputCanvas"></canvas>
      </div>
    </div>

    <div v-if="diseasePercentage !== null" class="analysis-result">
      <h2>分析结果</h2>
      <p>
        病害区域所占百分比：
        <strong :class="percentageClass">{{ diseasePercentage.toFixed(2) }}%</strong>
      </p>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import type cv from 'opencv-js';

// --- 响应式状态定义 ---
const opencvReady = ref(false);
const isProcessing = ref(false);
const originalImageUrl = ref<string | null>(null);
const diseasePercentage = ref<number | null>(null);
const imageLoaded = ref(false); // 标记图片是否已加载到<img>标签

// --- OpenCV.js 加载逻辑 ---
onMounted(() => {
  const script = document.createElement('script');
  script.src = '/opencv.js'; // 假设 opencv.js 在 public 目录下
  script.async = true;
  script.onload = () => {
    // cv 在 window 对象上变为可用
    (window as any).cv.onRuntimeInitialized = () => {
      console.log('OpenCV.js is ready.');
      opencvReady.value = true;
    };
  };
  document.body.appendChild(script);
});

// --- 文件处理 ---
const handleFileChange = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (target.files && target.files[0]) {
    const file = target.files[0];
    originalImageUrl.value = URL.createObjectURL(file);
    resetResults();
  }
};

const handleDrop = (event: DragEvent) => {
  if (event.dataTransfer && event.dataTransfer.files[0]) {
    const file = event.dataTransfer.files[0];
     if (file.type.startsWith('image/')) {
        originalImageUrl.value = URL.createObjectURL(file);
        resetResults();
     }
  }
};

const onImageLoad = () => {
  imageLoaded.value = true;
  // 图片加载完成后自动开始处理
  processImage();
};

const reset = () => {
    originalImageUrl.value = null;
    resetResults();
}

const resetResults = () => {
    diseasePercentage.value = null;
    imageLoaded.value = false;
    const canvas = document.getElementById('outputCanvas') as HTMLCanvasElement;
    if (canvas) {
        const ctx = canvas.getContext('2d');
        ctx?.clearRect(0, 0, canvas.width, canvas.height);
    }
}


// --- 核心图像处理函数 ---
const processImage = async () => {
  if (!opencvReady.value || !imageLoaded.value) return;

  isProcessing.value = true;
  diseasePercentage.value = null;

  // 使用setTimeout确保DOM更新，让加载状态显示出来
  setTimeout(() => {
    try {
      const cv = (window as any).cv as typeof import('opencv-js');
      const imgElement = document.getElementById('originalImage') as HTMLImageElement;
      if (!imgElement) {
          throw new Error("Cannot find the original image element.");
      }
      
      const src = cv.imread(imgElement);
      const hsv = new cv.Mat();
      cv.cvtColor(src, hsv, cv.COLOR_RGBA2RGB); // 如果是jpg则用RGBA2RGB, png可能需要RGBA2RGB
      cv.cvtColor(hsv, hsv, cv.COLOR_RGB2HSV);

      // 定义颜色范围 (与Python中的值一致)
      // 病变部分 (浅绿)
      const lightGreenLower = new cv.Mat(hsv.rows, hsv.cols, hsv.type(), [29, 50, 51, 0]);
      const lightGreenUpper = new cv.Mat(hsv.rows, hsv.cols, hsv.type(), [105, 211, 178, 255]);
      // 健康部分 (深绿)
      const darkGreenLower = new cv.Mat(hsv.rows, hsv.cols, hsv.type(), [0, 0, 0, 0]);
      const darkGreenUpper = new cv.Mat(hsv.rows, hsv.cols, hsv.type(), [29, 254, 208, 255]);
      
      const diseasedMask = new cv.Mat();
      const healthyMask = new cv.Mat();
      
      cv.inRange(hsv, lightGreenLower, lightGreenUpper, diseasedMask);
      cv.inRange(hsv, darkGreenLower, darkGreenUpper, healthyMask);

      // 形态学操作
      const kernel = cv.Mat.ones(5, 5, cv.CV_8U);
      const anchor = new cv.Point(-1, -1);
      cv.morphologyEx(diseasedMask, diseasedMask, cv.MORPH_OPEN, kernel, anchor, 1);
      cv.morphologyEx(diseasedMask, diseasedMask, cv.MORPH_CLOSE, kernel, anchor, 1);

      // 计算面积和百分比
      const diseasedArea = cv.countNonZero(diseasedMask);
      const healthyArea = cv.countNonZero(healthyMask);
      const totalArea = diseasedArea + healthyArea;
      
      diseasePercentage.value = totalArea > 0 ? (diseasedArea / totalArea) * 100 : 0;

      // 在输出图像上绘制轮廓
      const outputImage = src.clone();
      const contours = new cv.MatVector();
      const hierarchy = new cv.Mat();
      cv.findContours(diseasedMask, contours, hierarchy, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE);
      
      const redColor = new cv.Scalar(255, 0, 0, 255); // 红色
      for (let i = 0; i < contours.size(); ++i) {
        cv.drawContours(outputImage, contours, i, redColor, 2, cv.LINE_8, hierarchy, 100);
      }

      // 显示结果
      cv.imshow('outputCanvas', outputImage);

      // 释放内存
      src.delete();
      hsv.delete();
      lightGreenLower.delete();
      lightGreenUpper.delete();
      darkGreenLower.delete();
      darkGreenUpper.delete();
      diseasedMask.delete();
      healthyMask.delete();
      kernel.delete();
      contours.delete();
      hierarchy.delete();
      outputImage.delete();

    } catch (error) {
      console.error("Image processing error:", error);
      alert("图像处理失败，请检查控制台获取更多信息。");
    } finally {
      isProcessing.value = false;
    }
  }, 100); // 100ms延迟
};

// --- 计算属性，用于动态改变百分比颜色 ---
const percentageClass = computed(() => {
  if (diseasePercentage.value === null) return '';
  if (diseasePercentage.value > 25) return 'high';
  if (diseasePercentage.value > 10) return 'medium';
  return 'low';
});

</script>

<style>
:root {
  --primary-color: #4CAF50;
  --secondary-color: #f4f4f9;
  --border-color: #ddd;
  --text-color: #333;
  --danger-color: #f44336;
  --warning-color: #ff9800;
  --safe-color: #4CAF50;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
  background-color: var(--secondary-color);
  color: var(--text-color);
  margin: 0;
  padding: 20px;
  display: flex;
  justify-content: center;
}

.kelp-detector {
  width: 100%;
  max-width: 1200px;
  text-align: center;
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

header h1 {
  color: var(--primary-color);
  margin-bottom: 0.5rem;
}

header p {
  margin-top: 0;
  font-style: italic;
}

.loading-status { color: var(--warning-color); }
.ready-status { color: var(--safe-color); }

.upload-section {
  margin: 2rem 0;
}

.drop-area {
  border: 2px dashed var(--border-color);
  border-radius: 8px;
  padding: 2rem;
  transition: background-color 0.3s, border-color 0.3s;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
}

.drop-area:hover {
  border-color: var(--primary-color);
  background-color: #f9f9f9;
}

.upload-button, .re-upload-button {
  background-color: var(--primary-color);
  color: white;
  padding: 12px 24px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  transition: background-color 0.3s;
}
.upload-button:hover, .re-upload-button:hover {
  background-color: #45a049;
}

.re-upload-section {
  margin-bottom: 1rem;
}

.processing-status {
  margin: 2rem 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.spinner {
  border: 4px solid rgba(0,0,0,0.1);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border-left-color: var(--primary-color);
  animation: spin 1s ease infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}


.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
  margin-top: 2rem;
}

.image-card {
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 1rem;
  background-color: #fdfdfd;
}

.image-card h3 {
  margin-top: 0;
}

.image-card img, .image-card canvas {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
}

.analysis-result {
  margin-top: 2.5rem;
  padding: 1.5rem;
  background-color: var(--secondary-color);
  border-radius: 8px;
}

.analysis-result h2 {
  margin-top: 0;
}
.analysis-result p {
  font-size: 1.2rem;
}
.analysis-result strong {
  font-size: 1.5rem;
  font-weight: bold;
}

.analysis-result .high { color: var(--danger-color); }
.analysis-result .medium { color: var(--warning-color); }
.analysis-result .low { color: var(--safe-color); }
</style>