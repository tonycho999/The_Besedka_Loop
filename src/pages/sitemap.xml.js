const posts = import.meta.glob('./blog/*.md', { eager: true });

export async function GET() {
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
    
    // 👇 [핵심 수정 구간] 
    // 파이썬 봇이 쓴 "2026-03-01 01:30:01" 텍스트에서 공백을 기준으로 
    // 앞부분("2026-03-01")만 잘라서 구글 표준에 맞춥니다.
    let date = new Date().toISOString().split('T'); // 날짜가 없을 때의 기본값
    if (post.frontmatter.date) {
      date = String(post.frontmatter.date).split(' ');
    }
    
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
