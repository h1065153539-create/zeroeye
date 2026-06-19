import { refreshTokens } from './auth';
import * as api from './api';

// Mock the api module
jest.mock('./api', () => ({
  post: jest.fn(),
  get: jest.fn(),
  del: jest.fn(),
}));

describe('Auth Service - Single-Flight Token Refresh', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Reset local state if needed
    localStorage.clear();
  });

  it('should coalesce multiple concurrent refresh calls into a single API request', async () => {
    // Setup mock to return a delayed promise to simulate network latency
    const mockPost = api.post as jest.Mock;
    let resolveApi: (value: any) => void;
    mockPost.mockReturnValueOnce(
      new Promise((resolve) => {
        resolveApi = resolve;
      })
    );

    // Mock local storage tokens so it thinks we have a refresh token
    localStorage.setItem(
      'tot_auth_tokens',
      JSON.stringify({ accessToken: 'old-access', refreshToken: 'valid-refresh', expiresIn: 3600 })
    );

    // Trigger multiple refresh calls concurrently
    const p1 = refreshTokens();
    const p2 = refreshTokens();
    const p3 = refreshTokens();

    expect(p1).toBe(p2);
    expect(p2).toBe(p3);

    // API should only have been called ONCE
    expect(mockPost).toHaveBeenCalledTimes(1);

    // Resolve the API call
    const newTokens = { accessToken: 'new-access', refreshToken: 'new-refresh', expiresIn: 3600 };
    resolveApi!({ data: { tokens: newTokens } });

    // Wait for promises to resolve
    const [res1, res2, res3] = await Promise.all([p1, p2, p3]);

    // All callers should receive the identical updated tokens
    expect(res1).toEqual(newTokens);
    expect(res2).toEqual(newTokens);
    expect(res3).toEqual(newTokens);
  });

  it('should allow a new refresh call if the previous one failed', async () => {
    const mockPost = api.post as jest.Mock;
    mockPost.mockRejectedValueOnce(new Error('Network error'));

    localStorage.setItem(
      'tot_auth_tokens',
      JSON.stringify({ accessToken: 'old', refreshToken: 'valid', expiresIn: 3600 })
    );

    // First call fails
    const p1 = refreshTokens();
    const res1 = await p1;
    expect(res1).toBeNull();
    expect(mockPost).toHaveBeenCalledTimes(1);

    // Next call should trigger a new API request because the in-flight promise was cleared
    mockPost.mockResolvedValueOnce({
      data: { tokens: { accessToken: 'new2', refreshToken: 'new2', expiresIn: 3600 } },
    });

    const p2 = refreshTokens();
    const res2 = await p2;
    expect(res2).toEqual({ accessToken: 'new2', refreshToken: 'new2', expiresIn: 3600 });
    expect(mockPost).toHaveBeenCalledTimes(2);
  });
});
