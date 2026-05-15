import axios, { AxiosInstance } from 'axios';
import { LoadingPlan, Product, ScenarioInfo, Trailer } from '../types';

const BASE_URL = process.env.REACT_APP_API_URL ?? 'http://localhost:8000';

const http: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface ImportResult {
  importedCount: number;
  errors: string[];
  products: Product[];
}

export interface OptimizeRequest {
  trailerId: string;
  products: Product[];
}

const api = {
  /**
   * Return list of available demo scenario names and descriptions.
   */
  getScenarios: async (): Promise<ScenarioInfo[]> => {
    const response = await http.get<ScenarioInfo[]>('/api/scenarios');
    return response.data;
  },

  /**
   * Return all available trailer definitions.
   */
  getTrailers: async (): Promise<Trailer[]> => {
    const response = await http.get<Trailer[]>('/api/trailers');
    return response.data;
  },

  /**
   * Run optimizer for a named demo scenario.
   */
  optimizeScenario: async (name: string): Promise<LoadingPlan> => {
    const response = await http.get<LoadingPlan>(`/api/scenarios/${name}/optimize`);
    return response.data;
  },

  /**
   * Run optimizer with a custom trailer and product list.
   */
  optimizeCustom: async (trailerId: string, products: Product[]): Promise<LoadingPlan> => {
    const body: OptimizeRequest = { trailerId, products };
    const response = await http.post<LoadingPlan>('/api/optimize', body);
    return response.data;
  },

  /**
   * Upload an Excel file and receive parsed product list.
   */
  importExcel: async (file: File): Promise<ImportResult> => {
    const form = new FormData();
    form.append('file', file);
    const response = await http.post<ImportResult>('/api/import/excel', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },

  /**
   * Health check.
   */
  healthCheck: async (): Promise<boolean> => {
    try {
      await http.get('/health');
      return true;
    } catch {
      return false;
    }
  },
};

export default api;
