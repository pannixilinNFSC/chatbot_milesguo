1. Done 复习整理当前项目
2. Done 重做chunk，加大页间重叠范围
3. Done 改用elastic serverless
4. Done 每个chunk用LLM增加context
5. Done 多级检索，
1） 一阶搜索，得到chunks1
2.1）文档级语义检索，在summary页语义检索，得到top100
2.2）让LLM定位到10以下相关文档
2.3）相关文档的chunk，语义检索得到chunks2



