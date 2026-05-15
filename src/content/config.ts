import { defineCollection, z } from 'astro:content';

const blogCollection = defineCollection({
  type: 'content', // 마크다운 파일들의 모음임을 명시
  schema: z.object({
    title: z.string(),
    description: z.string(),
    pubDate: z.date(),
    image: z.string().optional(), // Pexels API에서 가져온 이미지 URL
    category: z.string(),
    tags: z.array(z.string()),
    keywords: z.string().optional(), // SEO용 키워드
  }),
});

export const collections = {
  'blog': blogCollection,
};
