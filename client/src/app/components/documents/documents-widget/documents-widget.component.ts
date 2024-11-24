import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { BsDropdownModule } from 'ngx-bootstrap/dropdown';
import { PaginationModule } from 'ngx-bootstrap/pagination';
import { ProgressbarModule } from 'ngx-bootstrap/progressbar';


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
}
