import { Redis } from '@upstash/redis';

const redis = new Redis({
  url: process.env.KV_REST_API_URL,
  token: process.env.KV_REST_API_TOKEN,
});

export default async function handler(req, res) {
  try {
    const stats = await redis.get('stats');

    if (!stats) {
      return res.status(200).json({ tbs_shared: 0, codes_detected: 0, servers_joined: 0 });
    }

    // If it's already an object (not a string), skip parsing
    const parsedStats = typeof stats === 'string' ? JSON.parse(stats) : stats;

    res.status(200).json(parsedStats);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
}
