import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { BsDropdownModule } from 'ngx-bootstrap/dropdown';
import { PaginationModule } from 'ngx-bootstrap/pagination';
import { ProgressbarModule } from 'ngx-bootstrap/progressbar';
import { FileService } from '../../../_services/file.service';
import { BlockchainService } from '../../../_services/blockchain.service';
import { NodeService } from '../../../_services/node.service';


@Component({
  selector: 'app-documents-widget',
  standalone: true,
  imports: [CommonModule,BsDropdownModule,PaginationModule,ProgressbarModule],
  templateUrl: './documents-widget.component.html',
  styleUrl: './documents-widget.component.css'
})
export class DocumentsWidgetComponent {
  currentPage = 1;
  totalItems = 64;
  selectedFile: File | null = null;
  private fileService= inject(FileService);
  private blockchainService = inject(BlockchainService);
  private nodeService = inject(NodeService);
  documents: any;
  nodeStatuses = this.blockchainService.nodeStatuses$;
  
  transactions: any;
  //documents = signal<any[]>([]);
  uploadFile(): void {
    if (this.selectedFile) {
      this.fileService.uploadFile(this.selectedFile).subscribe(
   
      );
    }
  }

  onFileSelected(event: any): void {
    const file: File = event.target.files[0]; 
    if (file) {
      this.selectedFile = file;
    }
 }

 corruptNode(node: any){
  console.log("node", node);
  this.nodeService.disableNode(node).subscribe(x =>
    console.log("x", x)
  )
 }

 corruptHash(node: any){
  console.log("node", node);
  this.nodeService.corruptHash(node).subscribe(x =>
    console.log("x", x)
  )
 }

 corruptFile(node: any){
  console.log("node", node);
  this.nodeService.corruptFile(node).subscribe(x =>
    console.log("x", x)
  )
 }

}