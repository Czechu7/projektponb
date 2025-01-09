import { HttpClient } from '@angular/common/http';
import { HubConnection, HubConnectionBuilder } from '@microsoft/signalr';
import { inject, Injectable, signal } from '@angular/core';
import { User } from '../_models/user';
import { Observable } from 'rxjs/internal/Observable';
import { BehaviorSubject } from 'rxjs';
import { NodeStatus } from '../_models/nodeStatus';

@Injectable({
  providedIn: 'root'
})

export class BlockchainService {
  private hubConnection: HubConnection | undefined;
  private http = inject(HttpClient);
  private baseUrl = 'http://localhost:4999/api';
  private readonly healthCheckInterval = 5000;
  
  nodeStatuses = signal<NodeStatus[]>([]);
  private nodeStatusesSubject = new BehaviorSubject<NodeStatus[]>([]);
  public nodeStatuses$ = this.nodeStatusesSubject.asObservable();

  constructor() {
    this.setupSignalRConnection();
  }

  private setupSignalRConnection() {
    this.hubConnection = new HubConnectionBuilder()
      .withUrl('http://localhost:4999/blockchainhub')
      .withAutomaticReconnect()
      .build();

    this.hubConnection.on('ReceiveNodeStatus', (nodeAddress: string, status: string) => {
      const currentStatuses = this.nodeStatusesSubject.value;
      const nodeIndex = currentStatuses.findIndex(n => n.address === nodeAddress);
      
      if (nodeIndex !== -1) {
        const updatedStatuses = [...currentStatuses];
        updatedStatuses[nodeIndex] = {
          ...updatedStatuses[nodeIndex],
          status,
          lastUpdate: new Date()
        };
        this.nodeStatusesSubject.next(updatedStatuses);
        this.nodeStatuses.set(updatedStatuses);
      }
    });

    this.hubConnection.onclose(() => {
      this.markNodesInactive();
    });

    this.startConnection();
    this.startHealthCheck();
  }

  private async startConnection() {
    try {
      if (this.hubConnection) {
        await this.hubConnection.start();
        console.log('SignalR Connected');
        this.loadInitialStatuses();
      }
    } catch (err) {
      console.error('Error while establishing connection: ', err);
      setTimeout(() => this.startConnection(), 5000);
    }
  }

  private loadInitialStatuses() {
    this.http.get<NodeStatus[]>(`${this.baseUrl}/nodes`).subscribe({
      next: (statuses) => {
        this.nodeStatusesSubject.next(statuses);
        this.nodeStatuses.set(statuses);
      },
      error: (error) => console.error('Error fetching node statuses:', error)
    });
  }

  private markNodesInactive() {
    const currentStatuses = this.nodeStatusesSubject.value;
    const updatedStatuses = currentStatuses.map(node => ({
      ...node,
      status: 'inactive',
      lastUpdate: new Date()
    }));
    this.nodeStatusesSubject.next(updatedStatuses);
    this.nodeStatuses.set(updatedStatuses);
  }
  private startHealthCheck() {
    setInterval(() => {
      const threshold = new Date(Date.now() - 30000); // 30 seconds threshold
      const currentStatuses = this.nodeStatusesSubject.value;
      let needsUpdate = false;

      const updatedStatuses = currentStatuses.map(node => {
        if (node.status === 'active' && new Date(node.lastUpdate) < threshold) {
          needsUpdate = true;
          return { ...node, status: 'inactive', lastUpdate: new Date() };
        }
        return node;
      });

      if (needsUpdate) {
        this.nodeStatusesSubject.next(updatedStatuses);
        this.nodeStatuses.set(updatedStatuses);
      }
    }, this.healthCheckInterval);
  }

  public getNodeStatuses(): Observable<NodeStatus[]> {
    return this.nodeStatuses$;
  }

  public isNodeActive(nodeAddress: string): boolean {
    const node = this.nodeStatusesSubject.value.find(n => n.address === nodeAddress);
    return node?.status === 'active';
  }

  public getActiveNodesCount(): number {
    return this.nodeStatusesSubject.value.filter(node => node.status === 'active').length;
  }

  public getNodeStatus(nodeAddress: string): NodeStatus | undefined {
    return this.nodeStatusesSubject.value.find(n => n.address === nodeAddress);
  }
}
