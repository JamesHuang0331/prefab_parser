import yaml
from typing import Dict
from yaml.parser import Parser
from yaml.reader import Reader
from yaml.scanner import Scanner
from yaml.composer import Composer
from yaml.constructor import Constructor
from yaml.resolver import Resolver

UnityTagPrefix = "tag:unity3d.com,2011:"


class PrefabNode:
    FileID: str
    NodeDict: Dict

    def __init__(self, file_id: str, node: yaml.Node):
        self.FileID = file_id
        self.NodeDict = node


class _PrefabParserInner(Parser):
    DEFAULT_TAGS = {'!u!': 'tag:unity3d.com,2011:'}
    DEFAULT_TAGS.update(Parser.DEFAULT_TAGS)


class PrefabComposer(Composer):
    def compose_document(self):
        """
        这里拷贝了基类的代码。注意！！这里的self传的是Loader类！！这是什么高级用法。。。
        :param _PrefabLoaderInner self:
        :return:
        """
        self.get_event()
        # Compose the root node.
        node = self.compose_node(None, None)
        # Drop the DOCUMENT-END event.
        self.get_event()

        # 在这里记录anchor和node的关系
        for anchor in self.anchors:
            node = self.anchors[anchor]
            self.m_dictFileID2NodeData[anchor] = self.construct_mapping(node)
            self.dictNode2FileID[node] = anchor

        self.anchors = {}
        return node


class _PrefabLoaderInner(Reader, Scanner, _PrefabParserInner, PrefabComposer, Constructor, Resolver):
    m_dictFileID2NodeData: Dict[str, Dict]
    """缓存anchor与node数据的对应关系"""
    dictNode2FileID: Dict[yaml.Node, str]

    def __init__(self, stream):
        self.m_dictFileID2NodeData = {}
        self.dictNode2FileID = {}

        Reader.__init__(self, stream)
        Scanner.__init__(self)
        _PrefabParserInner.__init__(self)
        PrefabComposer.__init__(self)
        Constructor.__init__(self)
        Resolver.__init__(self)


def _multi_constructor(loader: _PrefabLoaderInner, suffix: str, node: yaml.Node):
    file_id = loader.dictNode2FileID[node]
    return PrefabNode(file_id, loader.construct_mapping(node))


class PrefabParser:
    """构建一个类"""

    _dictFileID2NodeData: Dict[str, Dict]
    """缓存anchor与node数据的对应关系"""

    def __init__(self, stream: str):
        self._dictFileID2NodeData = {}
        self._serialize(stream)

    def _serialize(self, stream: str):
        """根据传入的字符串分割prefab，并生成fileId为key，节点数据的dict为value的dict"""

        _PrefabLoaderInner.add_multi_constructor(UnityTagPrefix, _multi_constructor)

        all_prefab_nodes = yaml.load_all(stream, _PrefabLoaderInner)

        for prefab_node in all_prefab_nodes:
            self._dictFileID2NodeData[prefab_node.FileID] = prefab_node.NodeDict

        return self._dictFileID2NodeData

    def get_obj(self, file_id: str):
        """根据file_id获取到对应的节点"""
        return self._dictFileID2NodeData.get(file_id, None)

    def __str__(self):
        return str(self._dictFileID2NodeData)

    def __iter__(self):
        return iter(self._dictFileID2NodeData)
