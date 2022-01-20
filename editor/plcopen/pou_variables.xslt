<?xml version="1.0"?>
<xsl:stylesheet xmlns:exsl="http://exslt.org/common" xmlns:xhtml="http://www.w3.org/1999/xhtml" xmlns:ppx="http://www.plcopen.org/xml/tc6_0201" xmlns:ns="beremiz" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" extension-element-prefixes="ns" version="1.0" exclude-result-prefixes="ns">
  <xsl:output method="xml"/>
  <xsl:template match="text()"/>
  <xsl:template mode="var_class" match="text()"/>
  <xsl:template mode="var_type" match="text()"/>
  <xsl:template mode="var_edit" match="text()"/>
  <xsl:template mode="var_debug" match="text()"/>
  <xsl:variable name="project" select="ns:GetProject()"/>
  <xsl:variable name="stdlib" select="ns:GetStdLibs()"/>
  <xsl:variable name="extensions" select="ns:GetExtensions()"/>
  <xsl:variable name="all_types" select="($project | $stdlib | $extensions)/ppx:types"/>
  <xsl:template name="add_root">
    <xsl:param name="class"/>
    <xsl:param name="type"/>
    <xsl:param name="edit">
      <xsl:text>true</xsl:text>
    </xsl:param>
    <xsl:param name="debug">
      <xsl:text>true</xsl:text>
    </xsl:param>
    <xsl:value-of select="ns:SetRoot($class, $type, $edit, $debug)"/>
  </xsl:template>
  <xsl:template match="ppx:pou">
    <xsl:call-template name="add_root">
      <xsl:with-param name="class">
        <xsl:value-of select="@pouType"/>
      </xsl:with-param>
      <xsl:with-param name="type">
        <xsl:value-of select="@name"/>
      </xsl:with-param>
    </xsl:call-template>
    <xsl:apply-templates select="ppx:interface"/>
    <xsl:apply-templates mode="variable_list" select="ppx:actions/ppx:action | ppx:transitions/ppx:transition"/>
  </xsl:template>
  <xsl:template match="ppx:action">
    <xsl:call-template name="add_root">
      <xsl:with-param name="class">
        <xsl:text>action</xsl:text>
      </xsl:with-param>
    </xsl:call-template>
    <xsl:apply-templates select="ancestor::ppx:pou/child::ppx:interface"/>
  </xsl:template>
  <xsl:template match="ppx:transition">
    <xsl:call-template name="add_root">
      <xsl:with-param name="class">
        <xsl:text>transition</xsl:text>
      </xsl:with-param>
    </xsl:call-template>
    <xsl:apply-templates select="ancestor::ppx:pou/child::ppx:interface"/>
  </xsl:template>
  <xsl:template match="ppx:configuration">
    <xsl:call-template name="add_root">
      <xsl:with-param name="class">
        <xsl:text>configuration</xsl:text>
      </xsl:with-param>
      <xsl:with-param name="debug">
        <xsl:text>false</xsl:text>
      </xsl:with-param>
    </xsl:call-template>
    <xsl:apply-templates mode="variable_list" select="ppx:resource"/>
    <xsl:apply-templates select="ppx:globalVars"/>
  </xsl:template>
  <xsl:template match="ppx:resource">
    <xsl:call-template name="add_root">
      <xsl:with-param name="class">
        <xsl:text>resource</xsl:text>
      </xsl:with-param>
      <xsl:with-param name="debug">
        <xsl:text>false</xsl:text>
      </xsl:with-param>
    </xsl:call-template>
    <xsl:apply-templates mode="variable_list" select="ppx:pouInstance | ppx:task/ppx:pouInstance"/>
    <xsl:apply-templates select="ppx:globalVars"/>
  </xsl:template>
  <xsl:template name="variables_infos">
    <xsl:param name="var_class"/>
    <xsl:for-each select="ppx:variable">
      <xsl:variable name="class">
        <xsl:apply-templates mode="var_class" select="ppx:type">
          <xsl:with-param name="default_class">
            <xsl:value-of select="$var_class"/>
          </xsl:with-param>
        </xsl:apply-templates>
      </xsl:variable>
      <xsl:variable name="type">
        <xsl:apply-templates mode="var_type" select="ppx:type"/>
      </xsl:variable>
      <xsl:variable name="edit">
        <xsl:apply-templates mode="var_edit" select="ppx:type"/>
      </xsl:variable>
      <xsl:variable name="debug">
        <xsl:apply-templates mode="var_debug" select="ppx:type"/>
      </xsl:variable>
      <xsl:value-of select="ns:AddVariable(@name, $class, $type, $edit, $debug)"/>
    </xsl:for-each>
  </xsl:template>
  <xsl:template match="ppx:localVars">
    <xsl:call-template name="variables_infos">
      <xsl:with-param name="var_class">
        <xsl:text>Local</xsl:text>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>
  <xsl:template match="ppx:globalVars">
    <xsl:call-template name="variables_infos">
      <xsl:with-param name="var_class">
        <xsl:text>Global</xsl:text>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>
  <xsl:template match="ppx:externalVars">
    <xsl:call-template name="variables_infos">
      <xsl:with-param name="var_class">
        <xsl:text>External</xsl:text>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>
  <xsl:template match="ppx:tempVars">
    <xsl:call-template name="variables_infos">
      <xsl:with-param name="var_class">
        <xsl:text>Temp</xsl:text>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>
  <xsl:template match="ppx:inputVars">
    <xsl:call-template name="variables_infos">
      <xsl:with-param name="var_class">
        <xsl:text>Input</xsl:text>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>
  <xsl:template match="ppx:outputVars">
    <xsl:call-template name="variables_infos">
      <xsl:with-param name="var_class">
        <xsl:text>Output</xsl:text>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>
  <xsl:template match="ppx:inOutVars">
    <xsl:call-template name="variables_infos">
      <xsl:with-param name="var_class">
        <xsl:text>InOut</xsl:text>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>
  <xsl:template name="add_variable">
    <xsl:param name="name"/>
    <xsl:param name="class"/>
    <xsl:param name="type"/>
    <xsl:param name="edit">
      <xsl:text>true</xsl:text>
    </xsl:param>
    <xsl:param name="debug">
      <xsl:text>true</xsl:text>
    </xsl:param>
    <xsl:value-of select="ns:AddVariable($name, $class, $type, $edit, $debug)"/>
  </xsl:template>
  <xsl:template mode="variable_list" match="ppx:action">
    <xsl:call-template name="add_variable">
      <xsl:with-param name="name">
        <xsl:value-of select="@name"/>
      </xsl:with-param>
      <xsl:with-param name="class">
        <xsl:text>action</xsl:text>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>
  <xsl:template mode="variable_list" match="ppx:transition">
    <xsl:call-template name="add_variable">
      <xsl:with-param name="name">
        <xsl:value-of select="@name"/>
      </xsl:with-param>
      <xsl:with-param name="class">
        <xsl:text>transition</xsl:text>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>
  <xsl:template mode="variable_list" match="ppx:resource">
    <xsl:call-template name="add_variable">
      <xsl:with-param name="name">
        <xsl:value-of select="@name"/>
      </xsl:with-param>
      <xsl:with-param name="class">
        <xsl:text>resource</xsl:text>
      </xsl:with-param>
      <xsl:with-param name="debug">
        <xsl:text>false</xsl:text>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>
  <xsl:template mode="variable_list" match="ppx:pouInstance">
    <xsl:call-template name="add_variable">
      <xsl:with-param name="name">
        <xsl:value-of select="@name"/>
      </xsl:with-param>
      <xsl:with-param name="class">
        <xsl:text>program</xsl:text>
      </xsl:with-param>
      <xsl:with-param name="type">
        <xsl:value-of select="@typeName"/>
      </xsl:with-param>
    </xsl:call-template>
  </xsl:template>
  <xsl:template mode="var_class" match="*[self::ppx:type or self::ppx:baseType]/ppx:derived">
    <xsl:param name="default_class"/>
    <xsl:variable name="type_name" select="@name"/>
    <xsl:variable name="pou_infos" select="$all_types/ppx:pous/ppx:pou[@name=$type_name]"/>
    <xsl:choose>
      <xsl:when test="$pou_infos">
        <xsl:apply-templates mode="var_class" select="$pou_infos"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$default_class"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  <xsl:template mode="var_class" match="ppx:pou">
    <xsl:value-of select="@pouType"/>
  </xsl:template>
  <xsl:template mode="var_class" match="*[self::ppx:type or self::ppx:baseType]/*">
    <xsl:param name="default_class"/>
    <xsl:value-of select="$default_class"/>
  </xsl:template>
  <xsl:template mode="var_type" match="*[self::ppx:type or self::ppx:baseType]/ppx:derived">
    <xsl:value-of select="@name"/>
  </xsl:template>
  <xsl:template mode="var_type" match="*[self::ppx:type or self::ppx:baseType]/ppx:array">
    <xsl:text>ARRAY [</xsl:text>
    <xsl:for-each select="ppx:dimension">
      <xsl:value-of select="@lower"/>
      <xsl:text>..</xsl:text>
      <xsl:value-of select="@upper"/>
    </xsl:for-each>
    <xsl:text>] OF </xsl:text>
    <xsl:apply-templates mode="var_type" select="ppx:baseType"/>
  </xsl:template>
  <xsl:template mode="var_type" match="*[self::ppx:type or self::ppx:baseType]/ppx:string">
    <xsl:text>STRING</xsl:text>
  </xsl:template>
  <xsl:template mode="var_type" match="*[self::ppx:type or self::ppx:baseType]/ppx:wstring">
    <xsl:text>WSTRING</xsl:text>
  </xsl:template>
  <xsl:template mode="var_type" match="*[self::ppx:type or self::ppx:baseType]/*">
    <xsl:value-of select="local-name()"/>
  </xsl:template>
  <xsl:template mode="var_edit" match="*[self::ppx:type or self::ppx:baseType]/ppx:derived">
    <xsl:variable name="type_name" select="@name"/>
    <xsl:variable name="pou_infos" select="$project/ppx:types/ppx:pous/ppx:pou[@name=$type_name]"/>
    <xsl:choose>
      <xsl:when test="$pou_infos">
        <xsl:text>true</xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text>false</xsl:text>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  <xsl:template mode="var_edit" match="*[self::ppx:type or self::ppx:baseType]/ppx:array">
    <xsl:apply-templates mode="var_edit" select="ppx:baseType"/>
  </xsl:template>
  <xsl:template mode="var_edit" match="*[self::ppx:type or self::ppx:baseType]/*">
    <xsl:text>false</xsl:text>
  </xsl:template>
  <xsl:template mode="var_debug" match="*[self::ppx:type or self::ppx:baseType]/ppx:derived">
    <xsl:variable name="type_name" select="@name"/>
    <xsl:variable name="datatype_infos" select="             $project/ppx:types/ppx:pous/ppx:pou[@name=$type_name] |             $all_types/ppx:dataTypes/ppx:dataType[@name=$type_name]         "/>
    <xsl:choose>
      <xsl:when test="$datatype_infos">
        <xsl:apply-templates mode="var_debug" select="$datatype_infos"/>
      </xsl:when>
      <xsl:otherwise>
        <xsl:text>false</xsl:text>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>
  <xsl:template mode="var_debug" match="ppx:pou">
    <xsl:text>true</xsl:text>
  </xsl:template>
  <xsl:template mode="var_debug" match="*[self::ppx:type or self::ppx:baseType]/ppx:array">
    <xsl:text>false</xsl:text>
  </xsl:template>
  <xsl:template mode="var_debug" match="*[self::ppx:type or self::ppx:baseType]/ppx:struct">
    <xsl:text>false</xsl:text>
  </xsl:template>
  <xsl:template mode="var_debug" match="*[self::ppx:type or self::ppx:baseType]/*">
    <xsl:text>true</xsl:text>
  </xsl:template>
</xsl:stylesheet>
