const posts = import.meta.glob('./blog/*.md', { eager: true });

export async function GET() {
  // 👇 에러 해결: 주소를 여기서 직접 변수로 선언합니다.
  const site = 'https://the-besedka-loop.vercel.app';
  const baseUrl = site.replace(/\/$/, '');

  // 1. 고정 페이지들
  const staticPages = [
    '',
    '/about'
  ];

  // 2. 블로그 글 페이지들
  const blogPages = Object.values(posts).map(post => {
    const slug = post.file.split('/').pop().replace('.md', '');
    const date = post.frontmatter.date || new Date().toISOString().split('T')[0];
    
    return `
      <url>
        <loc>${baseUrl}/blog/${slug}</loc>
        <lastmod>${date}</lastmod>
      </url>
    `.trim();
  });

  // 3. XML 조합
  const sitemap = `
    <?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      ${staticPages.map(path => `<url><loc>${baseUrl}${path}</loc></url>`).join('')}
      ${blogPages.join('')}
    </urlset>
  `.trim();

  return new Response(sitemap, {
    headers: {
      'Content-Type': 'application/xml',
    },
  });
}
