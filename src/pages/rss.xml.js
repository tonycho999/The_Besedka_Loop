import rss, { pagesGlobToRssItems } from '@astrojs/rss';

export async function GET(context) {
  return rss({
    // 1. RSS 피드 제목
    title: 'The Besedka Loop',
    // 2. 설명
    description: 'Signals from 10 scattered colleagues.',
    // 3. 사이트 주소 (astro.config.mjs의 site 값을 가져옴)
    site: context.site,
    // 4. 블로그 글 목록 가져오기 (경로에 주의하세요!)
    // 만약 글이 src/content/blog에 있다면 getCollection을 써야 하지만,
    // 현재 구조(src/pages/blog/*.md)라면 아래 방식이 맞습니다.
    items: await pagesGlobToRssItems(import.meta.glob('./blog/*.md')),
    customData: `<language>en-us</language>`,
  });
}
