import { get } from '@vercel/edge-config';

export const config = {
  runtime: 'edge',
};

export default async function handler(req) {
  const statsRaw = await get('stats');
  const stats = JSON.parse(statsRaw || '{}');

  return new Response(JSON.stringify(stats), {
    headers: { 'Content-Type': 'application/json' },
  });
}
