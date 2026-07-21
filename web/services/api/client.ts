export interface RequestOptions {
  headers?: Record<string, string>;
  body?: any;
  params?: Record<string, string>;
}

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(message: string, status: number, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

class ApiClient {
  private baseUrl: string = '/api/v1';
  private getAuthToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('abhedya_auth_token');
    }
    return null;
  }

  private async request<T>(method: string, path: string, options: RequestOptions = {}): Promise<T> {
    // Add realistic network delay
    await new Promise((resolve) => setTimeout(resolve, 300));

    // Simulate Interceptor: Attach Auth Header
    const token = this.getAuthToken();
    const headers = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...options.headers,
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };

    // Construct URL with search parameters
    let url = `${this.baseUrl}${path}`;
    if (options.params) {
      const searchParams = new URLSearchParams(options.params);
      url += `?${searchParams.toString()}`;
    }

    // In a real implementation:
    // const response = await fetch(url, { method, headers, body: JSON.stringify(options.body) });
    // if (!response.ok) throw new ApiError(response.statusText, response.status);
    // return response.json();

    // Since this is the initial frontend shell, we mock execution log traces
    if (process.env.NODE_ENV === 'development') {
      console.log(`[API CLIENT] [${method}] ${url}`, {
        headers,
        body: options.body,
      });
    }

    return {} as T;
  }

  public get<T>(path: string, options?: RequestOptions): Promise<T> {
    return this.request<T>('GET', path, options);
  }

  public post<T>(path: string, options?: RequestOptions): Promise<T> {
    return this.request<T>('POST', path, options);
  }

  public put<T>(path: string, options?: RequestOptions): Promise<T> {
    return this.request<T>('PUT', path, options);
  }

  public delete<T>(path: string, options?: RequestOptions): Promise<T> {
    return this.request<T>('DELETE', path, options);
  }

  public patch<T>(path: string, options?: RequestOptions): Promise<T> {
    return this.request<T>('PATCH', path, options);
  }
}

export const apiClient = new ApiClient();
export default apiClient;
