<template>
  <div class="min-h-screen bg-gray-100 flex flex-col items-center justify-center p-4">
    <div class="w-full max-w-4xl mx-auto bg-white rounded-lg shadow-md p-6">
      <h1 class="text-2xl font-bold text-center mb-6">海带病害智能检测与分析</h1>

      <!-- 加载状态提示 -->
      <div v-if="!isCvReady" class="text-center p-4 mb-4 bg-yellow-100 text-yellow-800 rounded-lg">
        <p>正在加载图像处理引擎 (OpenCV.js)，请稍候...</p>
      </div>

      <!-- 图片上传区域 -->
      <div class="mb-6">
        <label for="file-upload" class="block text-sm font-medium text-gray-700 mb-2">上传图片进行分析</label>
        <div class="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
          <div class="space-y-1 text-center">
            <svg class="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48" aria-hidden="true">
              <path d="M28 8H12a4 4
 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
            <div class="flex text-sm text-gray-600">
              <label for="file-upload" :class="['relative cursor-pointer bg-white rounded-md font-medium text-indigo-600 hover:text-indigo-500 focus-within:outline-none', { 'opacity-50 cursor-not-allowed': !isCvReady }]">
                <span>上传文件</span>
                <input id="file-upload" name="file-upload" type="file" class="sr-only" @change="handleImageUpload" :disabled="!isCvReady || isProcessing" accept="image/png, image/jpeg, image/jpg">
              </label>
              <p class="pl-1">或拖拽到此处</p>
            </div>
            <p class="text-xs text-gray-500">支持 PNG, JPG, JPEG 格式</p>
          </div>
        </div>
      </div>

      <!-- 处理中提示 -->
      <div v-if="isProcessing" class="text-center p-4 text-gray-600">
        <p>正在分析图片，请稍候...</p>
      </div>

      <!-- 结果展示区域 -->
      <div v-if="originalImage" class="space-y-6">
        <!-- 图片对比 -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h2 class="text-lg font-semibold mb-2">原始图片</h2>
            <img :src="originalImage" alt="Original Image" class="w-full h-auto rounded-lg shadow">
          </div>
          <div>
            <h2 class="text-lg font-semibold mb-2">分割标注图片</h2>
            <canvas ref="canvasOutput" class="w-full h-auto rounded-lg shadow"></canvas>
          </div>
        </div>

        <!-- 分析报告 -->
        <div v-if="analysisReport" class="bg-gray-50 p-4 rounded-lg shadow">
          <h2 class="text-lg font-semibold mb-3 border-b pb-2">检测分析报告</h2>
          <div class="text-center mb-4">
            <p class="text-sm text-gray-600">病害区域占比</p>
            <p class="text-4xl font-bold" :class="{'text-red-600': diseasePercentage > 10, 'text-yellow-600': diseasePercentage > 0, 'text-green-600': diseasePercentage === 0}">
              {{ diseasePercentage }}%
            </p>
          </div>
          <div class="bg-white p-4 rounded">
            <h3 class="font-semibold mb-2">详细报告：</h3>
            <pre class="whitespace-pre-wrap text-sm text-gray-800 font-sans">{{ analysisReport }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import cv from '@techstark/opencv-js';

// --- 响应式状态定义 ---
const isCvReady = ref(false);
const isProcessing = ref(false);
const originalImage = ref<string | null>(null);
const canvasOutput = ref<HTMLCanvasElement | null>(null);
const diseasePercentage = ref<number | null>(null);
const analysisReport = ref<string | null>(null);

// --- 生命周期钩子 ---
onMounted(() => {
  cv.then(() => {
    isCvReady.value = true;
    console.log('OpenCV.js is ready.');
  }).catch(err => {
    console.error('Failed to load OpenCV.js', err);
  });
});

// --- 方法定义 ---
const handleImageUpload = (event: Event) => {
  const target = event.target as HTMLInputElement;
  if (!target.files || !target.files[0]) return;
  const file = target.files[0];
  originalImage.value = null;
  diseasePercentage.value = null;
  analysisReport.value = null;
  if(canvasOutput.value){
      const ctx = canvasOutput.value.getContext('2d');
      ctx?.clearRect(0, 0, canvasOutput.value.width, canvasOutput.value.height);
  }
  const reader = new FileReader();
  reader.onload = (e) => {
    originalImage.value = e.target?.result as string;
    setTimeout(() => processImage(file), 0);
  };
  reader.readAsDataURL(file);
};

const generateReport = (percentage: number, fileName?: string) => {
    const now = new Date();
    const detectionTime = now.toLocaleString('zh-CN');
    const imageName = fileName || 'N/A';
    let conclusion = '';
    let suggestion = '';
    if (percentage === 0) {
        conclusion = '未检测到明显病变区域。';
        suggestion = '植株健康，请继续保持当前养殖环境。';
    } else if (percentage > 0 && percentage <= 10) {
        conclusion = '轻度感染。';
        suggestion = '建议进行隔离观察，并可考虑使用适量广谱杀菌剂进行预防性处理。注意水质和光照条件。';
    } else if (percentage > 10 && percentage <= 30) {
        conclusion = '中度感染。';
        suggestion = '病变已扩散，建议立即隔离病株，并使用针对性的杀菌剂进行治疗。同时检查养殖密度和水体营养盐平衡。';
    } else {
        conclusion = '重度感染。';
        suggestion = '病变非常严重，可能已无法治愈。建议立即移除并销毁病株，以防感染其他健康植株。对整个养殖环境进行彻底消毒。';
    }
    analysisReport.value = `
检测时间: ${detectionTime}
原始文件: ${imageName}
---------------------------------
[分析结论]
${conclusion}

[处理建议]
${suggestion}
---------------------------------
    `.trim().replace(/^\s+/gm, '');
};

const processImage = (file: File) => {
  if (!originalImage.value || !canvasOutput.value || !window.cv) {
    console.error('依赖未就绪，无法处理图片。');
    return;
  }
  isProcessing.value = true;
  const cv = window.cv;
  const image = new Image();
  image.src = originalImage.value;
  image.onload = () => {
    let src, hsv, diseasedMask, healthyMask, kernel, contours, hierarchy, outputImage;
    try {
      src = cv.imread(image);
      hsv = new cv.Mat();
      cv.cvtColor(src, hsv, cv.COLOR_RGBA2HSV, 0);
      let lightGreenLower = new cv.Scalar(29, 50, 51);
      let lightGreenUpper = new cv.Scalar(105, 211, 178);
      let darkGreenLower = new cv.Scalar(0, 0, 0);
      let darkGreenUpper = new cv.Scalar(29, 254, 208);
      diseasedMask = new cv.Mat();
      healthyMask = new cv.Mat();
      cv.inRange(hsv, lightGreenLower, lightGreenUpper, diseasedMask);
      cv.inRange(hsv, darkGreenLower, darkGreenUpper, healthyMask);
      const diseasedArea = cv.countNonZero(diseasedMask);
      const healthyArea = cv.countNonZero(healthyMask);
      const totalArea = diseasedArea + healthyArea;
      if (totalArea > 0) {
          const percentage = (diseasedArea / totalArea) * 100;
          diseasePercentage.value = parseFloat(percentage.toFixed(2));
      } else {
          diseasePercentage.value = 0;
      }
      generateReport(diseasePercentage.value, file.name);
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
      console.error('图像处理时发生错误:', error);
      analysisReport.value = "图像处理失败，请检查图片格式或联系技术支持。";
    } finally {
      src?.delete();
      hsv?.delete();
      diseasedMask?.delete();
      healthyMask?.delete();
      kernel?.delete();
      contours?.delete();
      hierarchy?.delete();
      outputImage?.delete();
      isProcessing.value = false;
    }
  };
  image.onerror = (err) => {
    console.error("图片加载失败。", err);
    isProcessing.value = false;
  }
};
</script>

<style>
pre {
  font-family: 'Courier New', Courier, monospace;
  line-height: 1.6;
}
</style>