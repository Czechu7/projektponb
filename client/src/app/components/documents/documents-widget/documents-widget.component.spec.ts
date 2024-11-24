import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DocumentsWidgetComponent } from './documents-widget.component';

describe('DocumentsWidgetComponent', () => {
  let component: DocumentsWidgetComponent;
  let fixture: ComponentFixture<DocumentsWidgetComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [DocumentsWidgetComponent]
    })
    .compileComponents();
    
    fixture = TestBed.createComponent(DocumentsWidgetComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
