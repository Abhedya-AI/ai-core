import { ApiError } from './client';

export type RequestInterceptor = (config: any) => any | Promise<any>;
export type ResponseInterceptor = (response: any) => any | Promise<any>;
export type ErrorInterceptor = (error: ApiError) => any | Promise<any>;

const requestInterceptors: RequestInterceptor[] = [
  (config) => {
    // Perform actions before request is sent
    return config;
  },
];

const responseInterceptors: ResponseInterceptor[] = [
  (response) => {
    // Perform actions on successful response data
    return response;
  },
];

const errorInterceptors: ErrorInterceptor[] = [
  (error) => {
    // Handle specific status codes
    if (error.status === 401) {
      console.warn('[API INTERCEPTOR] Unauthorized request, redirecting to login');
      if (typeof window !== 'undefined') {
        window.location.href = '/session-expired';
      }
    }
    if (error.status === 403) {
      console.warn('[API INTERCEPTOR] Forbidden request, redirecting to unauthorized');
      if (typeof window !== 'undefined') {
        window.location.href = '/unauthorized';
      }
    }
    return Promise.reject(error);
  },
];

export const interceptors = {
  request: requestInterceptors,
  response: responseInterceptors,
  error: errorInterceptors,
};
