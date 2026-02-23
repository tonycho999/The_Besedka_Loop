// 블로그 글 파일들을 모두 가져옵니다
const posts = import.meta.glob('./blog/*.md', { eager: true });

export async function GET({ site }) {
  const baseUrl = site.replace(/\/$/, ''); // 주소 끝에 / 제거

  // 1. 고정 페이지들 (Home, About)
  const staticPages = [
    '',
    '/about'
  ];

  // 2. 블로그 글 페이지들 (자동 생성)
  const blogPages = Object.values(posts).map(post => {
    // 파일 경로에서 slug(주소) 추출
    const slug = post.file.split('/').pop().replace('.md', '');
    const date = post.frontmatter.date || new Date().toISOString().split('T')[0];
    
    return `
      <url>
        <loc>${baseUrl}/blog/${slug}</loc>
        <lastmod>${date}</lastmod>
      </url>
    `.trim();
  });

  // 3. XML 형식으로 조합
  const sitemap = `
    <?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      ${staticPages.map(path => `<url><loc>${baseUrl}${path}</loc></url>`).join('')}
      ${blogPages.join('')}
    </urlset>
  `.trim();

  // 4. 파일 응답 (Response)
  return new Response(sitemap, {
    headers: {
      'Content-Type': 'application/xml',
    },
  });
}
