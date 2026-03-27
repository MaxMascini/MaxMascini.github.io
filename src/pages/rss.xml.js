import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';

export async function GET(context) {
  const posts = await getCollection('blog', ({ data }) => !data.draft);
  posts.sort((a, b) => new Date(b.data.date) - new Date(a.data.date));

  return rss({
    title: 'MinMaxed — Max Mascini',
    description: 'CS researcher, backpacker, and neuroscience grad exploring AI ethics and human-AI interaction.',
    site: context.site,
    items: posts.map((post) => ({
      title: post.data.title,
      pubDate: new Date(post.data.date),
      description: post.data.description,
      link: `/blog/${post.slug}/`,
    })),
  });
}
