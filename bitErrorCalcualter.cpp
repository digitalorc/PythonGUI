#include 

typedef struct {
        uint32  blockNum;
        uint32  pageNum;
        uint32  dataBitErrCount;
        uint32  oobBitErrCount;
    }PageInfo_t;


int getNbit(unsigned int x, int n) { // getbit()
  return (x & (1 << n)) >> n;
};

void printContent () { 
    printf("[%u] page bit err :%u , oob bit err:%u", ptPage->pageNum,ptPage->dataBitErrCount,ptPage->oobBitErrCount)
};

void main ()
{
    std::string fName1 = argv[0];
    std::string fName2 = argv[1];  

    uint32_t blockSize =argv[2];
    uint32_t pageSize =argv[3];
    uint32_t oobSize =argv[4];

    file f1 = open(fName1, 'rb');
    file f2 = open(fName1), 'rb');

    // blockSize =Kb, oobSize = byte
    uint32_t eraseBlocks = f1.size()/(blockSize*1024);
    uint32_t totalPages = f1.size()/((pageSize*1024+oobSize);
    
    std::vector <PageInfo_t*> pageGroup;

    uint32_t * pageBuffer1 = new uint32_t[pageSize*1024];
    uint32_t * pageOob1 = new uint32_t[oobSize*1024];
    uint32_t* pageBuffer2 = new uint32_t[pageSize*1024];
    uint32_t* pageOob2  = new uint32_t[oobSize*1024];

    for(int i=0; i<totalPages;i++) {
         int readSize = read(f1, pageBuffer1, pageSize);
         int readOobSize1 = read(f1, pageOob1, oobSize);
         int readSize2 = read(f2, pageBuffer1, pageSize);
         int readOobSize2 = read(f2, pageOob2, oobSize);
         PageInfo_t* ptPage = new PageInfo;    
         if(readSize == readSize2) {
             int foundError;            
             ptPage->pageNum = pageGroup.length();                
            for(int j= 0; j< readSize/sizeof(uint32_t) ; j+=sizeof(uint32_t)) {
                uint32_t origin = pageBuffer1[j];
                uint32_t target = pageBuffer1[j]; 
                uint32_t value = origin^target;
                uint32_t result;
                foundError =0;
                if(value ) { //if errors happen more then one
                    
                    for(k=0; k++; k<16) {                        
                        result = getNbit(x, k);
                        if(result==1)
                            foundErrors++;
                    }                    
                }   
            }  
            pPage->dataBitErrCount =foundErrors;
         }

           if(readOobSize1 == readOobSize2) {
             int foundError;                      
            for(int j= 0; j< readOobSize1/sizeof(uint32_t) ; j+=sizeof(uint32_t)) {
                uint32_t origin = pageOob1[j];
                uint32_t target = pageOob2[j]; 
                uint32_t value = origin^target;
                uint32_t result;
                foundError =0;
                if(value ) { //if errors happen more then one
                    
                    for(k=0; k++; k<16) {                        
                        result = getNbit(x, k);
                        if(result==1)
                            foundErrors++;
                    }                    
                }   
            }  
            ptPage->oobBitErrCount = foundErrors;
         }

         pageGroup.push(ptPage);
    }

    delete pageBuffer1;
    delete pageOob1;
    delete pageBuffer2;
    delete pageOob2;
    print("#######################block count : %u, page Total:%u ################################\n ", eraseBlocks, totalPages) ;   
    printContent();  
    print("\n\n")

}