import { Redis } from '@upstash/redis';

const redis = new Redis({
  url: process.env.UPSTASH_REDIS_REST_URL,
  token: process.env.UPSTASH_REDIS_REST_TOKEN,
});

export default async function handler(req, res) {
  try {
    const stats = await redis.get('stats');
    if (!stats) {
      return res.status(200).json({ tbs_shared: 0, codes_detected: 0, servers_joined: 0 });
    }
    res.status(200).json(JSON.parse(stats));
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}
