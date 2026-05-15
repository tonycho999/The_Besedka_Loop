/** @type {import('tailwindcss').Config} */
export default {
  // src 폴더 안에 있는 모든 astro, md, js 등의 파일에서 디자인 클래스를 찾으라는 명령어입니다.
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {},
  },
  plugins: [],
}
