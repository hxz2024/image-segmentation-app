<template>
  <div class="min-h-screen bg-gray-100 flex flex-col items-center justify-center p-4">
    <div class="w-full max-w-2xl mx-auto bg-white rounded-lg shadow-md p-6">
      <h1 class="text-2xl font-bold text-center mb-6">海带病害图像分割</h1>

      <!-- 加载状态提示 -->
      <div v-if="!isCvReady" class="text-center p-4 bg-yellow-100 text-yellow-800 rounded-lg">
        <p>正在加载图像处理引擎 (OpenCV.js)，请稍候...</p>
      </div>

      <!-- 图片上传区域 -->
      <div class="mb-6">
        <label for="file-upload" class="block text-sm font-medium text-gray-700 mb-2">上传图片</label>
        <div class="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
          <div class="space-y-1 text-center">
            <svg class="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48" aria-hidden="true">
              <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
            <div class="flex text-sm text-gray-600">
              <label for="file-upload" :class="['relative cursor-pointer bg-white rounded-md font-medium text-indigo-600 hover:text-indigo-500 focus-within:outline-none', { 'opacity-50 cursor-not-allowed': !isCvReady }]">
                <span>上传文件</span>
                <input id="file-upload" name="file-upload" type="file" class="sr-only" @change="handleImageUpload" :disabled="!isCvReady || isProcessing">
              </label>
              <p class="pl-1">或拖拽到此处</p>
            </div>
            <p class="text-xs text-gray-500">
              支持 PNG, JPG, JPEG 格式
            </p>
          </div>
        </div>
      </div>

      <!-- 处理中提示 -->
      <div v-if="isProcessing" class="text-center p-4">
        <p>正在处理图片，请稍候...</p>
      </div>

      <!-- 图片处理结果 -->
      <div v-if="originalImage" class="grid grid-cols-1 md-grid-cols-2 gap-4">
        <div>
          <h2 class="text-lg font-semibold mb-2">原始图片</h2>
          <img :src="originalImage" alt="Original Image" class="w-full h-auto rounded-lg">
        </div>
        <div>
          <h2 class="text-lg font-semibold mb-2">分割后的图片</h2>
          <canvas ref="canvasOutput" class="w-full h-auto rounded-lg"></canvas>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue';
import cvPromise from '@techstark/opencv-js';

const isCvReady = ref(false);
const isProcessing = ref(false);
const originalImage = ref<string | null>(null);
const canvasOutput = ref<HTMLCanvasElement | null>(null);
let cvInstance: any = null;

onMounted(() => {
  // *** 关键修正 ***
  // 1. 使用 `(cvPromise as any)` 来告诉 TypeScript 忽略类型检查
  // 2. 为回调函数的参数 'cv' 和 'err' 添加 'any' 类型
  (cvPromise as any).then((cv: any) => {
    console.log('OpenCV.js is ready.');
    cvInstance = cv;
    isCvReady.value = true;
  }).catch((err: any) => {
    console.error('加载 OpenCV.js 失败:', err);
  });
});

const handleImageUpload = (event: Event) => {
  const target = event.target as HTMLInputElement;
  const file = target.files?.[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (e) => {
    const imageUrl = e.target?.result as string;
    originalImage.value = imageUrl;
    
    nextTick(() => {
      processImage(imageUrl);
    });
  };
  reader.readAsDataURL(file);
};

const processImage = (imageUrl: string) => {
  if (!canvasOutput.value || !cvInstance) {
    console.error('依赖未就绪，中断图像处理。Canvas 或 cvInstance 未准备好。');
    return;
  }

  isProcessing.value = true;

  const image = new Image();
  image.src = imageUrl;
  image.onload = () => {
    const cv = cvInstance;
    
    let src, bgr, hsv, diseasedMask, healthyMask, kernel, contours, hierarchy, outputImage;
    let lightGreenLower, lightGreenUpper, darkGreenLower, darkGreenUpper;

    try {
      src = cv.imread(image);
      bgr = new cv.Mat();
      hsv = new cv.Mat();
      
      cv.cvtColor(src, bgr, cv.COLOR_RGBA2BGR);
      cv.cvtColor(bgr, hsv, cv.COLOR_BGR2HSV);

      diseasedMask = new cv.Mat();
      lightGreenLower = new cv.Mat(hsv.rows, hsv.cols, hsv.type(), new cv.Scalar(29, 50, 51, 0));
      lightGreenUpper = new cv.Mat(hsv.rows, hsv.cols, hsv.type(), new cv.Scalar(105, 211, 178, 255));
      cv.inRange(hsv, lightGreenLower, lightGreenUpper, diseasedMask);

      healthyMask = new cv.Mat();
      darkGreenLower = new cv.Mat(hsv.rows, hsv.cols, hsv.type(), new cv.Scalar(0, 0, 0, 0));
      darkGreenUpper = new cv.Mat(hsv.rows, hsv.cols, hsv.type(), new cv.Scalar(29, 254, 208, 255));
      cv.inRange(hsv, darkGreenLower, darkGreenUpper, healthyMask);

      kernel = cv.Mat.ones(5, 5, cv.CV_8U);
      cv.morphologyEx(diseasedMask, diseasedMask, cv.MORPH_OPEN, kernel);
      cv.morphologyEx(diseasedMask, diseasedMask, cv.MORPH_CLOSE, kernel);

      outputImage = src.clone();
      contours = new cv.MatVector();
      hierarchy = new cv.Mat();
      cv.findContours(diseasedMask, contours, hierarchy, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE);
      
      const redColor = new cv.Scalar(255, 0, 0, 255);
      for (let i = 0; i < contours.size(); ++i) {
        cv.drawContours(outputImage, contours, i, redColor, 2, cv.LINE_8, hierarchy, 100);
      }

      cv.imshow(canvasOutput.value, outputImage);

    } catch (error) {
      console.error('图像处理过程中发生错误:', error);
    } finally {
      src?.delete();
      bgr?.delete();
      hsv?.delete();
      diseasedMask?.delete();
      healthyMask?.delete();
      kernel?.delete();
      contours?.delete();
      hierarchy?.delete();
      outputImage?.delete();
      lightGreenLower?.delete();
      lightGreenUpper?.delete();
      darkGreenLower?.delete();
      darkGreenUpper?.delete();
      
      isProcessing.value = false;
    }
  };
  image.onerror = (err) => {
    console.error("加载图片到 Image 对象失败。", err);
    isProcessing.value = false;
  }
};
</script>
