export class Node {
  id: string;
  group?: number; // 可选属性，节点分组
  x?: number; // 可选属性，节点初始位置
  y?: number; // 可选属性，节点初始位置

  constructor(id: string, group?: number, x?: number, y?: number) {
    this.id = id;
    this.group = group;
    this.x = x;
    this.y = y;
  }
}

export class Link {
  source: string; // 起始节点ID
  target: string; // 目标节点ID
  value?: number; // 可选属性，边权重
  
  constructor(source: string, target: string, value?: number) {
    this.source = source;
    this.target = target;
    this.value = value;
  }
}